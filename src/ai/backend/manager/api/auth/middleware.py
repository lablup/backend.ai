"""
Auth middleware for unified authentication.

This module provides:
- Unified authentication middleware supporting JWT, HMAC, and hook authentication
- Authentication flow helpers for each auth method
"""

from __future__ import annotations

import functools
import logging
import secrets
from contextlib import ExitStack
from typing import TYPE_CHECKING, Any, Final

import sqlalchemy as sa
from aiohttp import web

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.common.jwt.exceptions import JWTError
from ai.backend.common.plugin.hook import FIRST_COMPLETED, PASSED
from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.utils import with_log_context_fields
from ai.backend.manager.api.utils import get_handler_attr
from ai.backend.manager.errors.auth import AuthorizationFailed, InvalidAuthParameters
from ai.backend.manager.errors.common import RejectedByHook
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.resource_policy import (
    keypair_resource_policies,
    user_resource_policies,
)
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import execute_with_retry

from .utils import _extract_auth_params, check_date, sign_request, validate_ip

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("auth_middleware",)


def _set_unauthenticated_state(request: web.Request) -> None:
    """Initialize request with unauthenticated state."""
    request["is_authorized"] = False
    request["is_admin"] = False
    request["is_superadmin"] = False
    request["keypair"] = None
    request["user"] = None


async def _query_cred_by_access_key(
    root_ctx: RootContext,
    access_key: str,
) -> tuple[Any, Any]:
    """
    Query keypair and user information by access_key.

    Returns:
        Tuple of (user_row, keypair_row) or (None, None) if not found
    """

    async with root_ctx.db.begin_readonly() as conn:
        # Query keypair with resource policy
        j = keypairs.join(
            keypair_resource_policies,
            keypairs.c.resource_policy == keypair_resource_policies.c.name,
        )
        query = (
            sa.select(keypairs, keypair_resource_policies)
            .set_label_style(sa.LABEL_STYLE_TABLENAME_PLUS_COL)
            .select_from(j)
            .where(
                (keypairs.c.access_key == access_key) & (keypairs.c.is_active.is_(True)),
            )
        )
        result = await conn.execute(query)
        keypair_row = result.first()

        if keypair_row is None:
            return None, None

        # Query user with resource policy by joining keypairs table
        j = users.join(
            user_resource_policies,
            users.c.resource_policy == user_resource_policies.c.name,
        ).join(
            keypairs,
            users.c.uuid == keypairs.c.user,
        )
        query = (
            sa.select(users, user_resource_policies)
            .set_label_style(sa.LABEL_STYLE_TABLENAME_PLUS_COL)
            .select_from(j)
            .where(keypairs.c.access_key == access_key)
        )
        result = await conn.execute(query)
        user_row = result.first()

        return user_row, keypair_row


def _populate_auth_result(
    request: web.Request,
    user_row: Any,
    keypair_row: Any,
) -> None:
    """
    Populate authentication result into request state.

    This function is called by all authentication flows (JWT, HMAC, Hook)
    to set up the common request state structure.
    """
    if not user_row or not keypair_row:
        return

    keypair_mapping = keypair_row._mapping
    user_mapping = user_row._mapping

    auth_result = {
        "is_authorized": True,
        "keypair": {
            col.name: keypair_mapping[f"keypairs_{col.name}"]
            for col in keypairs.c
            if col.name != "secret_key"
        },
        "user": {
            col.name: user_mapping[f"users_{col.name}"]
            for col in users.c
            if col.name not in ("password", "description", "created_at")
        },
        "is_admin": keypair_mapping["keypairs_is_admin"],
    }

    validate_ip(request, auth_result["user"])

    auth_result["keypair"]["resource_policy"] = {
        col.name: keypair_mapping[f"keypair_resource_policies_{col.name}"]
        for col in keypair_resource_policies.c
    }
    auth_result["user"]["resource_policy"] = {
        col.name: user_mapping[f"user_resource_policies_{col.name}"]
        for col in user_resource_policies.c
    }
    auth_result["user"]["id"] = keypair_mapping["keypairs_user_id"]  # legacy
    auth_result["is_superadmin"] = auth_result["user"]["role"] == "superadmin"

    # Populate the result to the per-request state dict
    request.update(auth_result)


async def _authenticate_via_jwt(
    request: web.Request,
    root_ctx: RootContext,
    jwt_token: str,
) -> None:
    """
    JWT token-based authentication flow.

    Used by GraphQL Federation (Hive Router) with stateless validation.
    JWT tokens are signed using per-user secret keys (from keypair table),
    maintaining the same security model as HMAC authentication.

    Args:
        request: aiohttp request
        root_ctx: Manager root context
        jwt_token: JWT token from X-BackendAI-Token header

    Raises:
        AuthorizationFailed: If JWT validation fails or access_key not found
    """
    import jwt as pyjwt

    try:
        # 1. Decode token without verification to extract access_key
        unverified_payload = pyjwt.decode(
            jwt_token,
            options={"verify_signature": False},
        )
        access_key = unverified_payload.get("access_key")
        if not access_key:
            raise AuthorizationFailed("Access key not found in JWT token")

        # 2. Query keypair and user from database to get secret_key
        user_row, keypair_row = await execute_with_retry(
            functools.partial(_query_cred_by_access_key, root_ctx, access_key)
        )

        if keypair_row is None:
            raise AuthorizationFailed("Access key not found in database")

        # 3. Validate JWT token using user's secret key
        secret_key = keypair_row.keypairs_secret_key
        root_ctx.jwt_validator.validate_token(jwt_token, secret_key)

        # 4. Populate authentication result
        _populate_auth_result(request, user_row, keypair_row)
        log.trace("JWT authentication succeeded for access_key={}", access_key)

        # 5. Update statistics
        await root_ctx.valkey_stat.increment_keypair_query_count(access_key)

    except JWTError as e:
        log.warning("JWT authentication failed: {}", e)
        raise AuthorizationFailed(f"JWT validation failed: {e}") from e


async def _authenticate_via_hmac(
    request: web.Request,
    root_ctx: RootContext,
) -> None:
    """
    HMAC signature-based authentication flow.

    Used by traditional REST API with Client SDK.

    Args:
        request: aiohttp request
        root_ctx: Manager root context

    Raises:
        InvalidAuthParameters: If date/time sync error or malformed header
        AuthorizationFailed: If signature mismatch or access_key not found
    """
    # 1. Check date/time sync
    if not check_date(request):
        raise InvalidAuthParameters("Date/time sync error")

    # 2. Extract HMAC parameters from Authorization header
    params = _extract_auth_params(request)
    if not params:
        # Unsigned requests (public APIs)
        return

    sign_method, access_key, signature = params

    # 3. Query keypair and user from database
    user_row, keypair_row = await execute_with_retry(
        functools.partial(_query_cred_by_access_key, root_ctx, access_key)
    )

    if keypair_row is None:
        raise AuthorizationFailed("Access key not found in HMAC")

    # 4. Verify HMAC signature
    my_signature = await sign_request(sign_method, request, keypair_row.keypairs_secret_key)

    if not secrets.compare_digest(my_signature, signature):
        raise AuthorizationFailed("HMAC signature mismatch")

    # 5. Populate authentication result
    _populate_auth_result(request, user_row, keypair_row)

    # 6. Update statistics
    await root_ctx.valkey_stat.increment_keypair_query_count(access_key)


async def _authenticate_via_hook(
    request: web.Request,
    root_ctx: RootContext,
) -> None:
    """
    Plugin hook-based authentication flow.

    Used for 3rd-party authentication (OAuth, SAML, etc).

    Args:
        request: aiohttp request
        root_ctx: Manager root context

    Raises:
        RejectedByHook: If hook rejects the request
        AuthorizationFailed: If access_key not found
    """
    # 1. Dispatch PRE_AUTH_MIDDLEWARE hook
    hook_result = await root_ctx.hook_plugin_ctx.dispatch(
        "PRE_AUTH_MIDDLEWARE",
        (request,),
        return_when=FIRST_COMPLETED,
    )

    if hook_result.status != PASSED:
        raise RejectedByHook.from_hook_result(hook_result)

    if not hook_result.result:
        # No hooks configured, unsigned request
        return

    # 2. Hook returns access_key (None means anonymous access)
    access_key = hook_result.result
    if access_key is None:
        # Anonymous access allowed
        return

    # 3. Query keypair and user from database
    user_row, keypair_row = await execute_with_retry(
        functools.partial(_query_cred_by_access_key, root_ctx, access_key)
    )

    if keypair_row is None:
        raise AuthorizationFailed("Access key not found in hook")

    # 4. Populate authentication result
    _populate_auth_result(request, user_row, keypair_row)

    # 5. Update statistics
    await root_ctx.valkey_stat.increment_keypair_query_count(access_key)


def _setup_user_context(request: web.Request) -> ExitStack:
    """
    Setup user context for logging and request tracking.

    Returns:
        ExitStack with user context managers
    """
    stack = ExitStack()

    if user := request.get("user"):
        user_id = user.get("uuid")
        if user_id is not None:
            stack.enter_context(
                with_user(
                    UserData(
                        user_id=user_id,
                        is_authorized=request.get("is_authorized", False),
                        is_admin=request.get("is_admin", False),
                        is_superadmin=request.get("is_superadmin", False),
                        role=request["user"]["role"],
                        domain_name=request["user"]["domain_name"],
                    )
                )
            )
            stack.enter_context(
                with_log_context_fields({
                    "user_id": str(user_id),
                })
            )

    return stack


@web.middleware
async def auth_middleware(request: web.Request, handler: Any) -> web.StreamResponse:
    """
    Unified authentication middleware - routes to appropriate authentication flow.

    This middleware detects the authentication method and dispatches to:
    - JWT authentication (X-BackendAI-Token header)
    - HMAC authentication (Authorization header)
    - Hook authentication (3rd-party plugins)
    """
    allow_list = request.app["auth_middleware_allowlist"]

    # Skip authentication for allowed paths
    if any(request.path.startswith(path) for path in allow_list):
        _set_unauthenticated_state(request)
        return await handler(request)

    # Initialize request state
    root_ctx: RootContext = request.app["_root.context"]
    _set_unauthenticated_state(request)

    # Skip if handler doesn't require authentication
    if not get_handler_attr(request, "auth_required", False):
        return await handler(request)

    # Detect authentication method and route to appropriate flow
    jwt_token = request.headers.get("X-BackendAI-Token")
    auth_header = request.headers.get("Authorization")
    if jwt_token:
        # JWT authentication flow (GraphQL Federation)
        await _authenticate_via_jwt(request, root_ctx, jwt_token)
    elif auth_header:
        # HMAC authentication flow (REST API)
        await _authenticate_via_hmac(request, root_ctx)
    else:
        # Hook authentication flow (3rd-party plugins)
        await _authenticate_via_hook(request, root_ctx)

    # Setup user context for logging
    with _setup_user_context(request):
        # Pass-through to handler (auth_required decorator validates authorization)
        return await handler(request)
