"""Authentication middleware and route-level authorization decorators.

This module contains:

* ``auth_middleware`` — a global (``web.middleware``) middleware that detects
  the authentication method (JWT / HMAC / hook) and populates the request
  with user credentials.

* ``auth_required``, ``admin_required``, ``superadmin_required`` —
  route-level decorators (usable as ``RouteMiddleware``) that enforce
  authorization requirements *after* the global middleware has already
  authenticated the request.

* ``*_for_method`` variants for class-based handlers.
"""

from __future__ import annotations

import functools
import hashlib
import hmac
import ipaddress
import logging
import secrets
from collections.abc import Awaitable, Callable, Mapping
from contextlib import ExitStack
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import urlparse

import jwt as pyjwt
import sqlalchemy as sa
from aiohttp import web
from aiohttp.typedefs import Handler
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.jwt.exceptions import JWTError
from ai.backend.common.plugin.hook import FIRST_COMPLETED, PASSED
from ai.backend.common.types import ReadableCIDR
from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.utils import with_log_context_fields
from ai.backend.manager.api.rest.types import WebRequestHandler
from ai.backend.manager.errors.auth import (
    AuthorizationFailed,
    InvalidAuthParameters,
    InvalidClientIPConfig,
)
from ai.backend.manager.errors.common import GenericForbidden, RejectedByHook
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.resource_policy import (
    keypair_resource_policies,
    user_resource_policies,
)
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import execute_with_retry

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_whois_timezone_info: Final = {
    "A": 1 * 3600,
    "ACDT": 10.5 * 3600,
    "ACST": 9.5 * 3600,
    "ACT": -5 * 3600,
    "ACWST": 8.75 * 3600,
    "ADT": 4 * 3600,
    "AEDT": 11 * 3600,
    "AEST": 10 * 3600,
    "AET": 10 * 3600,
    "AFT": 4.5 * 3600,
    "AKDT": -8 * 3600,
    "AKST": -9 * 3600,
    "ALMT": 6 * 3600,
    "AMST": -3 * 3600,
    "AMT": -4 * 3600,
    "ANAST": 12 * 3600,
    "ANAT": 12 * 3600,
    "AQTT": 5 * 3600,
    "ART": -3 * 3600,
    "AST": 3 * 3600,
    "AT": -4 * 3600,
    "AWDT": 9 * 3600,
    "AWST": 8 * 3600,
    "AZOST": 0 * 3600,
    "AZOT": -1 * 3600,
    "AZST": 5 * 3600,
    "AZT": 4 * 3600,
    "AoE": -12 * 3600,
    "B": 2 * 3600,
    "BNT": 8 * 3600,
    "BOT": -4 * 3600,
    "BRST": -2 * 3600,
    "BRT": -3 * 3600,
    "BST": 6 * 3600,
    "BTT": 6 * 3600,
    "C": 3 * 3600,
    "CAST": 8 * 3600,
    "CAT": 2 * 3600,
    "CCT": 6.5 * 3600,
    "CDT": -5 * 3600,
    "CEST": 2 * 3600,
    "CET": 1 * 3600,
    "CHADT": 13.75 * 3600,
    "CHAST": 12.75 * 3600,
    "CHOST": 9 * 3600,
    "CHOT": 8 * 3600,
    "CHUT": 10 * 3600,
    "CIDST": -4 * 3600,
    "CIST": -5 * 3600,
    "CKT": -10 * 3600,
    "CLST": -3 * 3600,
    "CLT": -4 * 3600,
    "COT": -5 * 3600,
    "CST": -6 * 3600,
    "CT": -6 * 3600,
    "CVT": -1 * 3600,
    "CXT": 7 * 3600,
    "ChST": 10 * 3600,
    "D": 4 * 3600,
    "DAVT": 7 * 3600,
    "DDUT": 10 * 3600,
    "E": 5 * 3600,
    "EASST": -5 * 3600,
    "EAST": -6 * 3600,
    "EAT": 3 * 3600,
    "ECT": -5 * 3600,
    "EDT": -4 * 3600,
    "EEST": 3 * 3600,
    "EET": 2 * 3600,
    "EGST": 0 * 3600,
    "EGT": -1 * 3600,
    "EST": -5 * 3600,
    "ET": -5 * 3600,
    "F": 6 * 3600,
    "FET": 3 * 3600,
    "FJST": 13 * 3600,
    "FJT": 12 * 3600,
    "FKST": -3 * 3600,
    "FKT": -4 * 3600,
    "FNT": -2 * 3600,
    "G": 7 * 3600,
    "GALT": -6 * 3600,
    "GAMT": -9 * 3600,
    "GET": 4 * 3600,
    "GFT": -3 * 3600,
    "GILT": 12 * 3600,
    "GMT": 0 * 3600,
    "GST": 4 * 3600,
    "GYT": -4 * 3600,
    "H": 8 * 3600,
    "HDT": -9 * 3600,
    "HKT": 8 * 3600,
    "HOVST": 8 * 3600,
    "HOVT": 7 * 3600,
    "HST": -10 * 3600,
    "I": 9 * 3600,
    "ICT": 7 * 3600,
    "IDT": 3 * 3600,
    "IOT": 6 * 3600,
    "IRDT": 4.5 * 3600,
    "IRKST": 9 * 3600,
    "IRKT": 8 * 3600,
    "IRST": 3.5 * 3600,
    "IST": 5.5 * 3600,
    "JST": 9 * 3600,
    "K": 10 * 3600,
    "KGT": 6 * 3600,
    "KOST": 11 * 3600,
    "KRAST": 8 * 3600,
    "KRAT": 7 * 3600,
    "KST": 9 * 3600,
    "KUYT": 4 * 3600,
    "L": 11 * 3600,
    "LHDT": 11 * 3600,
    "LHST": 10.5 * 3600,
    "LINT": 14 * 3600,
    "M": 12 * 3600,
    "MAGST": 12 * 3600,
    "MAGT": 11 * 3600,
    "MART": 9.5 * 3600,
    "MAWT": 5 * 3600,
    "MDT": -6 * 3600,
    "MHT": 12 * 3600,
    "MMT": 6.5 * 3600,
    "MSD": 4 * 3600,
    "MSK": 3 * 3600,
    "MST": -7 * 3600,
    "MT": -7 * 3600,
    "MUT": 4 * 3600,
    "MVT": 5 * 3600,
    "MYT": 8 * 3600,
    "N": -1 * 3600,
    "NCT": 11 * 3600,
    "NDT": 2.5 * 3600,
    "NFT": 11 * 3600,
    "NOVST": 7 * 3600,
    "NOVT": 7 * 3600,
    "NPT": 5.5 * 3600,
    "NRT": 12 * 3600,
    "NST": 3.5 * 3600,
    "NUT": -11 * 3600,
    "NZDT": 13 * 3600,
    "NZST": 12 * 3600,
    "O": -2 * 3600,
    "OMSST": 7 * 3600,
    "OMST": 6 * 3600,
    "ORAT": 5 * 3600,
    "P": -3 * 3600,
    "PDT": -7 * 3600,
    "PET": -5 * 3600,
    "PETST": 12 * 3600,
    "PETT": 12 * 3600,
    "PGT": 10 * 3600,
    "PHOT": 13 * 3600,
    "PHT": 8 * 3600,
    "PKT": 5 * 3600,
    "PMDT": -2 * 3600,
    "PMST": -3 * 3600,
    "PONT": 11 * 3600,
    "PST": -8 * 3600,
    "PT": -8 * 3600,
    "PWT": 9 * 3600,
    "PYST": -3 * 3600,
    "PYT": -4 * 3600,
    "Q": -4 * 3600,
    "QYZT": 6 * 3600,
    "R": -5 * 3600,
    "RET": 4 * 3600,
    "ROTT": -3 * 3600,
    "S": -6 * 3600,
    "SAKT": 11 * 3600,
    "SAMT": 4 * 3600,
    "SAST": 2 * 3600,
    "SBT": 11 * 3600,
    "SCT": 4 * 3600,
    "SGT": 8 * 3600,
    "SRET": 11 * 3600,
    "SRT": -3 * 3600,
    "SST": -11 * 3600,
    "SYOT": 3 * 3600,
    "T": -7 * 3600,
    "TAHT": -10 * 3600,
    "TFT": 5 * 3600,
    "TJT": 5 * 3600,
    "TKT": 13 * 3600,
    "TLT": 9 * 3600,
    "TMT": 5 * 3600,
    "TOST": 14 * 3600,
    "TOT": 13 * 3600,
    "TRT": 3 * 3600,
    "TVT": 12 * 3600,
    "U": -8 * 3600,
    "ULAST": 9 * 3600,
    "ULAT": 8 * 3600,
    "UTC": 0 * 3600,
    "UYST": -2 * 3600,
    "UYT": -3 * 3600,
    "UZT": 5 * 3600,
    "V": -9 * 3600,
    "VET": -4 * 3600,
    "VLAST": 11 * 3600,
    "VLAT": 10 * 3600,
    "VOST": 6 * 3600,
    "VUT": 11 * 3600,
    "W": -10 * 3600,
    "WAKT": 12 * 3600,
    "WARST": -3 * 3600,
    "WAST": 2 * 3600,
    "WAT": 1 * 3600,
    "WEST": 1 * 3600,
    "WET": 0 * 3600,
    "WFT": 12 * 3600,
    "WGST": -2 * 3600,
    "WGT": -3 * 3600,
    "WIB": 7 * 3600,
    "WIT": 9 * 3600,
    "WITA": 8 * 3600,
    "WST": 14 * 3600,
    "WT": 0 * 3600,
    "X": -11 * 3600,
    "Y": -12 * 3600,
    "YAKST": 10 * 3600,
    "YAKT": 9 * 3600,
    "YAPT": 10 * 3600,
    "YEKST": 6 * 3600,
    "YEKT": 5 * 3600,
    "Z": 0 * 3600,
}
whois_timezone_info: Final[Mapping[str, int]] = {k: int(v) for k, v in _whois_timezone_info.items()}

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def set_handler_attr(func: Any, key: str, value: Any) -> None:
    attrs = getattr(func, "_backend_attrs", None)
    if attrs is None:
        attrs = {}
    attrs[key] = value
    func._backend_attrs = attrs


def get_handler_attr(request: web.Request, key: str, default: Any = None) -> Any:
    attrs = getattr(request.match_info.handler, "_backend_attrs", None)
    if attrs is not None:
        return attrs.get(key, default)
    return default


def _extract_auth_params(request: web.Request) -> tuple[str, str, str] | None:
    """
    HTTP Authorization header must be formatted as:
    "Authorization: BackendAI signMethod=HMAC-SHA256,
                    credential=<ACCESS_KEY>:<SIGNATURE>"
    """
    auth_hdr = request.headers.get("Authorization")
    if not auth_hdr:
        return None
    pieces = auth_hdr.split(" ", 1)
    if len(pieces) != 2:
        raise InvalidAuthParameters("Malformed authorization header")
    auth_type, auth_str = pieces
    if auth_type not in ("BackendAI", "Sorna"):
        raise InvalidAuthParameters("Invalid authorization type name")

    raw_params = map(lambda s: s.strip(), auth_str.split(","))
    params = {}
    for param in raw_params:
        key, value = param.split("=", 1)
        params[key.strip()] = value.strip()

    try:
        access_key, signature = params["credential"].split(":", 1)
        return params["signMethod"], access_key, signature
    except (KeyError, ValueError) as e:
        raise InvalidAuthParameters("Missing or malformed authorization parameters") from e


def check_date(request: web.Request) -> bool:
    raw_date = request.headers.get("Date")
    if not raw_date:
        raw_date = request.headers.get("X-BackendAI-Date", request.headers.get("X-Sorna-Date"))
    if not raw_date:
        return False
    try:
        date = dtparse(raw_date, tzinfos=whois_timezone_info)
        if date.tzinfo is None:
            date = date.replace(tzinfo=tzutc())
        now = datetime.now(tzutc())
        min_date = now - timedelta(minutes=15)
        max_date = now + timedelta(minutes=15)
        request["date"] = date
        request["raw_date"] = raw_date
        if not (min_date < date < max_date):
            return False
    except ValueError:
        return False
    return True


async def sign_request(sign_method: str, request: web.Request, secret_key: str) -> str:
    try:
        mac_type, hash_type = map(lambda s: s.lower(), sign_method.split("-"))
        if mac_type != "hmac":
            raise InvalidAuthParameters("Unsupported request signing method (MAC type)")
        if hash_type not in hashlib.algorithms_guaranteed:
            raise InvalidAuthParameters("Unsupported request signing method (hash type)")

        new_api_version = request.headers.get("X-BackendAI-Version")
        legacy_api_version = request.headers.get("X-Sorna-Version")
        api_version = new_api_version or legacy_api_version
        if api_version is None:
            raise InvalidAuthParameters("API version missing in request headers")
        body = b""
        if api_version < "v4.20181215":
            if request.can_read_body and request.content_type != "multipart/form-data":
                body = await request.read()
        body_hash = hashlib.new(hash_type, body).hexdigest()
        path = request.raw_path
        host = request.host
        if upstream_url := request.headers.get("X-Forwarded-URL", None):
            parsed_url = urlparse(upstream_url)
            path = parsed_url.path
            host = parsed_url.netloc

        sign_bytes = "{0}\n{1}\n{2}\nhost:{3}\ncontent-type:{4}\nx-{name}-version:{5}\n{6}".format(
            request.method,
            str(path),
            request["raw_date"],
            host,
            request.content_type,
            api_version,
            body_hash,
            name="backendai" if new_api_version is not None else "sorna",
        ).encode()
        sign_key = hmac.new(
            secret_key.encode(), request["date"].strftime("%Y%m%d").encode(), hash_type
        ).digest()
        sign_key = hmac.new(sign_key, host.encode(), hash_type).digest()
        return hmac.new(sign_key, sign_bytes, hash_type).hexdigest()
    except ValueError as e:
        raise AuthorizationFailed("Invalid signature") from e


def validate_ip(request: web.Request, user: Mapping[str, Any]) -> None:
    allowed_client_ip = user.get("allowed_client_ip", None)
    if not allowed_client_ip or allowed_client_ip is None:
        return
    if not isinstance(allowed_client_ip, list):
        raise InvalidClientIPConfig("allowed_client_ip must be a list")
    raw_client_addr: str | None = request.headers.get("X-Forwarded-For") or request.remote
    if raw_client_addr is None:
        raise AuthorizationFailed("Not allowed IP address")
    try:
        client_addr: ReadableCIDR[ipaddress.IPv4Network | ipaddress.IPv6Network] = ReadableCIDR(
            raw_client_addr, is_network=False
        )
    except InvalidIpAddressValue as e:
        raise InvalidAuthParameters(f"{raw_client_addr} is invalid IP address value") from e
    if any(client_addr.address in allowed_ip_cand.address for allowed_ip_cand in allowed_client_ip):
        return
    raise AuthorizationFailed(f"'{client_addr}' is not allowed IP address")


# ---------------------------------------------------------------------------
# Internal authentication flows
# ---------------------------------------------------------------------------


def _set_unauthenticated_state(request: web.Request) -> None:
    request["is_authorized"] = False
    request["is_admin"] = False
    request["is_superadmin"] = False
    request["keypair"] = None
    request["user"] = None


async def _query_cred_by_access_key(
    root_ctx: RootContext,
    access_key: str,
) -> tuple[Any, Any]:
    async with root_ctx.db.begin_readonly() as conn:
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

    request.update(auth_result)


async def _authenticate_via_jwt(
    request: web.Request,
    root_ctx: RootContext,
    jwt_token: str,
) -> None:
    try:
        unverified_payload = pyjwt.decode(
            jwt_token,
            options={"verify_signature": False},
        )
        access_key = unverified_payload.get("access_key")
        if not access_key:
            raise AuthorizationFailed("Access key not found in JWT token")

        user_row, keypair_row = await execute_with_retry(
            functools.partial(_query_cred_by_access_key, root_ctx, access_key)
        )

        if keypair_row is None:
            raise AuthorizationFailed("Access key not found in database")

        secret_key = keypair_row.keypairs_secret_key
        root_ctx.jwt_validator.validate_token(jwt_token, secret_key)

        _populate_auth_result(request, user_row, keypair_row)
        log.trace("JWT authentication succeeded for access_key={}", access_key)

        await root_ctx.valkey_stat.increment_keypair_query_count(access_key)

    except JWTError as e:
        log.warning("JWT authentication failed: {}", e)
        raise AuthorizationFailed(f"JWT validation failed: {e}") from e


async def _authenticate_via_hmac(
    request: web.Request,
    root_ctx: RootContext,
) -> None:
    if not check_date(request):
        raise InvalidAuthParameters("Date/time sync error")

    params = _extract_auth_params(request)
    if not params:
        return

    sign_method, access_key, signature = params

    user_row, keypair_row = await execute_with_retry(
        functools.partial(_query_cred_by_access_key, root_ctx, access_key)
    )

    if keypair_row is None:
        raise AuthorizationFailed("Access key not found in HMAC")

    my_signature = await sign_request(sign_method, request, keypair_row.keypairs_secret_key)

    if not secrets.compare_digest(my_signature, signature):
        raise AuthorizationFailed("HMAC signature mismatch")

    _populate_auth_result(request, user_row, keypair_row)

    await root_ctx.valkey_stat.increment_keypair_query_count(access_key)


async def _authenticate_via_hook(
    request: web.Request,
    root_ctx: RootContext,
) -> None:
    hook_result = await root_ctx.hook_plugin_ctx.dispatch(
        "PRE_AUTH_MIDDLEWARE",
        (request,),
        return_when=FIRST_COMPLETED,
    )

    if hook_result.status != PASSED:
        raise RejectedByHook.from_hook_result(hook_result)

    if not hook_result.result:
        return

    access_key = hook_result.result
    if access_key is None:
        return

    user_row, keypair_row = await execute_with_retry(
        functools.partial(_query_cred_by_access_key, root_ctx, access_key)
    )

    if keypair_row is None:
        raise AuthorizationFailed("Access key not found in hook")

    _populate_auth_result(request, user_row, keypair_row)

    await root_ctx.valkey_stat.increment_keypair_query_count(access_key)


def _setup_user_context(request: web.Request) -> ExitStack:
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
                        role=UserRole(request["user"]["role"]),
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


# ---------------------------------------------------------------------------
# Global middleware
# ---------------------------------------------------------------------------


@web.middleware
async def auth_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    """Unified authentication middleware — routes to the appropriate auth flow."""
    allow_list = request.app["auth_middleware_allowlist"]

    if any(request.path.startswith(path) for path in allow_list):
        _set_unauthenticated_state(request)
        return await handler(request)

    root_ctx: RootContext = request.app["_root.context"]
    _set_unauthenticated_state(request)

    if not get_handler_attr(request, "auth_required", False):
        return await handler(request)

    jwt_token = request.headers.get("X-BackendAI-Token")
    auth_header = request.headers.get("Authorization")
    if jwt_token:
        await _authenticate_via_jwt(request, root_ctx, jwt_token)
    elif auth_header:
        await _authenticate_via_hmac(request, root_ctx)
    else:
        await _authenticate_via_hook(request, root_ctx)

    with _setup_user_context(request):
        return await handler(request)


# ---------------------------------------------------------------------------
# Route-level authorization decorators (usable as RouteMiddleware)
# ---------------------------------------------------------------------------


def auth_required(handler: WebRequestHandler) -> WebRequestHandler:
    @functools.wraps(handler)
    async def wrapped(request: web.Request) -> web.StreamResponse:
        if request.get("is_authorized", False):
            return await handler(request)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "user")
    return wrapped


def auth_required_for_method(
    method: Callable[..., Awaitable[web.StreamResponse]],
) -> Callable[..., Awaitable[web.StreamResponse]]:
    @functools.wraps(method)
    async def wrapped(
        self: Any, request: web.Request, *args: Any, **kwargs: Any
    ) -> web.StreamResponse:
        if request.get("is_authorized", False):
            return await method(self, request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "user")
    return wrapped


def admin_required(handler: WebRequestHandler) -> WebRequestHandler:
    @functools.wraps(handler)
    async def wrapped(request: web.Request, *args: Any, **kwargs: Any) -> web.StreamResponse:
        if not request.get("is_authorized", False):
            raise AuthorizationFailed("Unauthorized access")
        if not request.get("is_admin", False):
            raise GenericForbidden("Insufficient privileges")
        return await handler(request, *args, **kwargs)

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "admin")
    return wrapped


def admin_required_for_method(
    method: Callable[..., Awaitable[web.StreamResponse]],
) -> Callable[..., Awaitable[web.StreamResponse]]:
    @functools.wraps(method)
    async def wrapped(
        self: Any, request: web.Request, *args: Any, **kwargs: Any
    ) -> web.StreamResponse:
        if request.get("is_authorized", False) and request.get("is_admin", False):
            return await method(self, request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "admin")
    return wrapped


def superadmin_required(handler: WebRequestHandler) -> WebRequestHandler:
    @functools.wraps(handler)
    async def wrapped(request: web.Request, *args: Any, **kwargs: Any) -> web.StreamResponse:
        if not request.get("is_authorized", False):
            raise AuthorizationFailed("Unauthorized access")
        if not request.get("is_superadmin", False):
            raise GenericForbidden("Insufficient privileges")
        return await handler(request, *args, **kwargs)

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "superadmin")
    return wrapped


def superadmin_required_for_method(
    method: Callable[..., Awaitable[web.StreamResponse]],
) -> Callable[..., Awaitable[web.StreamResponse]]:
    @functools.wraps(method)
    async def wrapped(
        self: Any, request: web.Request, *args: Any, **kwargs: Any
    ) -> web.StreamResponse:
        if request.get("is_authorized", False) and request.get("is_superadmin", False):
            return await method(self, request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "superadmin")
    return wrapped
