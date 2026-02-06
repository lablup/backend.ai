from __future__ import annotations

import functools
import hashlib
import hmac
import ipaddress
import logging
import secrets
from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import ExitStack
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Any, Final
from urllib.parse import urlparse

import aiohttp_cors
import jwt as pyjwt
import sqlalchemy as sa
from aiohttp import web
from aiohttp.typedefs import Handler
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseResponseModel,
    BodyParam,
    QueryParam,
    api_handler,
)
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    GetRoleRequest,
    SignoutRequest,
    SignupRequest,
    UpdateFullNameRequest,
    UpdatePasswordNoAuthRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
    VerifyAuthRequest,
)
from ai.backend.common.dto.manager.auth.response import (
    AuthorizeResponse,
    GetRoleResponse,
    GetSSHKeypairResponse,
    SignoutResponse,
    SignupResponse,
    SSHKeypairResponse,
    UpdateFullNameResponse,
    UpdatePasswordNoAuthResponse,
    UpdatePasswordResponse,
)
from ai.backend.common.dto.manager.auth.types import (
    AuthResponseType,
    AuthSuccessResponse,
)
from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.jwt.exceptions import JWTError
from ai.backend.common.plugin.hook import FIRST_COMPLETED, PASSED
from ai.backend.common.types import ReadableCIDR
from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.utils import with_log_context_fields
from ai.backend.manager.errors.auth import (
    AuthorizationFailed,
    InvalidAuthParameters,
    InvalidClientIPConfig,
)
from ai.backend.manager.errors.common import RejectedByHook
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.resource_policy import (
    keypair_resource_policies,
    user_resource_policies,
)
from ai.backend.manager.models.user import users
from ai.backend.manager.models.utils import execute_with_retry
from ai.backend.manager.services.auth.actions.authorize import AuthorizeAction
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import GenerateSSHKeypairAction
from ai.backend.manager.services.auth.actions.get_role import GetRoleAction
from ai.backend.manager.services.auth.actions.get_ssh_keypair import GetSSHKeypairAction
from ai.backend.manager.services.auth.actions.signout import SignoutAction
from ai.backend.manager.services.auth.actions.signup import SignupAction
from ai.backend.manager.services.auth.actions.update_full_name import UpdateFullNameAction
from ai.backend.manager.services.auth.actions.update_password import UpdatePasswordAction
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthAction,
)
from ai.backend.manager.services.auth.actions.upload_ssh_keypair import UploadSSHKeypairAction

from .context import RootContext
from .types import CORSOptions, WebMiddleware
from .utils import get_handler_attr, set_handler_attr

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
        # HTTP standard says "Date" header must be in GMT only.
        # However, dateutil.parser can recognize other commonly used
        # timezone names and offsets.
        date = dtparse(raw_date, tzinfos=whois_timezone_info)
        if date.tzinfo is None:
            date = date.replace(tzinfo=tzutc())  # assume as UTC
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
                # read the whole body if neither streaming nor bodyless
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
        # allowed_client_ip is None or [] - empty list
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


@web.middleware
async def auth_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
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


def auth_required(handler: Handler) -> Handler:
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


def admin_required(handler: Handler) -> Handler:
    @functools.wraps(handler)
    async def wrapped(request: web.Request, *args: Any, **kwargs: Any) -> web.StreamResponse:
        if request.get("is_authorized", False) and request.get("is_admin", False):
            return await handler(request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "admin")
    return wrapped


def admin_required_for_method(
    method: Callable[..., Awaitable[web.StreamResponse]],
) -> Callable[..., Awaitable[web.StreamResponse]]:
    """Decorator for class methods that require admin authentication."""

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


def superadmin_required(handler: Handler) -> Handler:
    @functools.wraps(handler)
    async def wrapped(request: web.Request, *args: Any, **kwargs: Any) -> web.StreamResponse:
        if request.get("is_authorized", False) and request.get("is_superadmin", False):
            return await handler(request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "superadmin")
    return wrapped


def superadmin_required_for_method(
    method: Callable[..., Awaitable[web.StreamResponse]],
) -> Callable[..., Awaitable[web.StreamResponse]]:
    """Decorator for class methods that require superadmin authentication."""

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


# Deferred import to break circular dependency:
#   This module (api.auth) is imported by api.session for auth_required decorator.
#   Meanwhile, ProcessorsCtx lives in dto.context which transitively imports
#   api.session through: dto.context -> services.processors -> repositories
#   -> repositories.session.repository -> api.session -> api.auth (partially loaded).
#   Placing this import after auth_required ensures the decorator is already
#   defined when the circular chain resolves back here.
# TODO: Move find_dependency_sessions from api.session to repository layer
#       to eliminate this circular dependency entirely.
from ai.backend.manager.dto.context import ProcessorsCtx, RequestCtx, UserContext  # noqa: E402


class AuthAPIHandler:
    """REST API handler class for auth operations."""

    # Verify auth endpoint

    @auth_required_for_method
    @api_handler
    async def verify_auth(
        self,
        query: QueryParam[VerifyAuthRequest],
        user_ctx: UserContext,
    ) -> APIResponse:
        """Verify authentication status."""
        req = query.parsed
        log.info("AUTH.VERIFY(ak:{})", user_ctx.access_key)

        class TestResponse(BaseResponseModel):
            authorized: str
            echo: str

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestResponse(authorized="yes", echo=req.echo),
        )

    # Authorization endpoints

    async def authorize(
        self,
        request: web.Request,
    ) -> web.StreamResponse:
        """Authorize a user with domain, username, and password.

        Note: This endpoint doesn't use @api_handler because it may return
        a streaming response for 2FA flows.
        """
        # Parse request body with pydantic validation
        body = await request.json()
        req = AuthorizeRequest.model_validate(body)

        root_ctx: RootContext = request.app["_root.context"]
        processors = root_ctx.processors

        log.info(
            "AUTH.AUTHORIZE(d:{}, u:{}, passwd:****, type:{})",
            req.domain,
            req.username,
            req.type,
        )

        action = AuthorizeAction(
            request=request,
            type=req.type,
            domain_name=req.domain,
            email=req.username,
            password=req.password,
            stoken=req.stoken,
        )
        result = await processors.auth.authorize.wait_for_complete(action)

        # Handle streaming response (for 2FA flows)
        if result.stream_response is not None:
            return result.stream_response

        if result.authorization_result is None:
            raise AuthorizationFailed("Authorization result is missing")

        auth_result = result.authorization_result
        resp = AuthorizeResponse(
            data=AuthSuccessResponse(
                response_type=AuthResponseType.SUCCESS,
                access_key=auth_result.access_key,
                secret_key=auth_result.secret_key,
                role=auth_result.role,
                status=auth_result.status,
            )
        )
        return web.json_response(resp.model_dump(mode="json"), status=HTTPStatus.OK)

    @auth_required_for_method
    @api_handler
    async def get_role(
        self,
        query: QueryParam[GetRoleRequest],
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get user's role information."""
        req = query.parsed
        processors = processors_ctx.processors
        log.info(
            "AUTH.ROLES(ak:{}, d:{}, g:{})",
            user_ctx.access_key,
            user_ctx.user_domain,
            req.group,
        )

        # Get is_superadmin and is_admin from request context
        # These are set by auth middleware
        action = GetRoleAction(
            user_id=user_ctx.user_uuid,
            group_id=req.group,
            is_superadmin=False,  # Will be determined by service
            is_admin=False,  # Will be determined by service
        )
        result = await processors.auth.get_role.wait_for_complete(action)

        resp = GetRoleResponse(
            global_role=result.global_role,
            domain_role=result.domain_role,
            group_role=result.group_role,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @api_handler
    async def signup(
        self,
        body: BodyParam[SignupRequest],
        request_ctx: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Sign up a new user."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.SIGNUP(d:{}, email:{}, passwd:****)", req.domain, req.email)

        action = SignupAction(
            request=request_ctx.request,
            domain_name=req.domain,
            email=req.email,
            password=req.password,
            username=req.username,
            full_name=req.full_name,
            description=req.description,
        )
        result = await processors.auth.signup.wait_for_complete(action)

        resp = SignupResponse(
            access_key=result.access_key,
            secret_key=result.secret_key,
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def signout(
        self,
        body: BodyParam[SignoutRequest],
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Sign out a user."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.SIGNOUT(d:{}, email:{})", user_ctx.user_domain, req.email)

        action = SignoutAction(
            user_id=user_ctx.user_uuid,
            domain_name=user_ctx.user_domain,
            requester_email=user_ctx.user_email,
            email=req.email,
            password=req.password,
        )
        await processors.auth.signout.wait_for_complete(action)

        return APIResponse.build(status_code=HTTPStatus.OK, response_model=SignoutResponse())

    # Password management endpoints

    @auth_required_for_method
    @api_handler
    async def update_password(
        self,
        body: BodyParam[UpdatePasswordRequest],
        request_ctx: RequestCtx,
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update user's password (requires authentication)."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.UPDATE_PASSWORD(d:{}, email:{})", user_ctx.user_domain, user_ctx.user_email)

        action = UpdatePasswordAction(
            request=request_ctx.request,
            user_id=user_ctx.user_uuid,
            domain_name=user_ctx.user_domain,
            email=user_ctx.user_email,
            old_password=req.old_password,
            new_password=req.new_password,
            new_password_confirm=req.new_password2,
        )
        result = await processors.auth.update_password.wait_for_complete(action)

        if not result.success:
            return APIResponse.build(
                status_code=HTTPStatus.BAD_REQUEST,
                response_model=UpdatePasswordResponse(error_msg="new password mismatch"),
            )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=UpdatePasswordResponse())

    @api_handler
    async def update_password_no_auth(
        self,
        body: BodyParam[UpdatePasswordNoAuthRequest],
        request_ctx: RequestCtx,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update user's password without authentication (for expired passwords)."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info(
            "AUTH.UPDATE_PASSWORD_NO_AUTH(d:{}, u:{}, passwd:****)",
            req.domain,
            req.username,
        )

        action = UpdatePasswordNoAuthAction(
            request=request_ctx.request,
            domain_name=req.domain,
            email=req.username,
            current_password=req.current_password,
            new_password=req.new_password,
        )
        result = await processors.auth.update_password_no_auth.wait_for_complete(action)

        resp = UpdatePasswordNoAuthResponse(
            password_changed_at=result.password_changed_at.isoformat(),
        )
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def update_full_name(
        self,
        body: BodyParam[UpdateFullNameRequest],
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Update user's full name."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.UPDATE_FULL_NAME(d:{}, email:{})", user_ctx.user_domain, user_ctx.user_email)

        action = UpdateFullNameAction(
            user_id=str(user_ctx.user_uuid),
            full_name=req.full_name,
            domain_name=user_ctx.user_domain,
            email=user_ctx.user_email,
        )
        await processors.auth.update_full_name.wait_for_complete(action)

        return APIResponse.build(status_code=HTTPStatus.OK, response_model=UpdateFullNameResponse())

    # SSH keypair endpoints

    @auth_required_for_method
    @api_handler
    async def get_ssh_keypair(
        self,
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Get user's SSH public key."""
        processors = processors_ctx.processors
        log.info("AUTH.GET_SSH_KEYPAIR(d:{}, ak:{})", user_ctx.user_domain, user_ctx.access_key)

        action = GetSSHKeypairAction(
            user_id=user_ctx.user_uuid,
            access_key=user_ctx.access_key,
        )
        result = await processors.auth.get_ssh_keypair.wait_for_complete(action)

        resp = GetSSHKeypairResponse(
            ssh_public_key=result.public_key,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def generate_ssh_keypair(
        self,
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Generate a new SSH keypair for the user."""
        processors = processors_ctx.processors
        log.info("AUTH.REFRESH_SSH_KEYPAIR(d:{}, ak:{})", user_ctx.user_domain, user_ctx.access_key)

        action = GenerateSSHKeypairAction(
            user_id=user_ctx.user_uuid,
            access_key=user_ctx.access_key,
        )
        result = await processors.auth.generate_ssh_keypair.wait_for_complete(action)

        resp = SSHKeypairResponse(
            ssh_public_key=result.ssh_keypair.ssh_public_key,
            ssh_private_key=result.ssh_keypair.ssh_private_key,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    @auth_required_for_method
    @api_handler
    async def upload_ssh_keypair(
        self,
        body: BodyParam[UploadSSHKeypairRequest],
        user_ctx: UserContext,
        processors_ctx: ProcessorsCtx,
    ) -> APIResponse:
        """Upload a custom SSH keypair."""
        req = body.parsed
        processors = processors_ctx.processors
        log.info("AUTH.SAVE_SSH_KEYPAIR(d:{}, ak:{})", user_ctx.user_domain, user_ctx.access_key)

        # Normalize keypair format (ensure trailing newline)
        pubkey = f"{req.pubkey.rstrip()}\n"
        privkey = f"{req.privkey.rstrip()}\n"

        action = UploadSSHKeypairAction(
            user_id=user_ctx.user_uuid,
            public_key=pubkey,
            private_key=privkey,
            access_key=user_ctx.access_key,
        )
        result = await processors.auth.upload_ssh_keypair.wait_for_complete(action)

        resp = SSHKeypairResponse(
            ssh_public_key=result.ssh_keypair.ssh_public_key,
            ssh_private_key=result.ssh_keypair.ssh_private_key,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "auth"  # slashed to distinguish with "/vN/authorize"
    app["api_versions"] = (1, 2, 3, 4, 5)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    handler = AuthAPIHandler()
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", handler.verify_auth))
    cors.add(root_resource.add_route("POST", handler.verify_auth))
    test_resource = cors.add(app.router.add_resource("/test"))
    cors.add(test_resource.add_route("GET", handler.verify_auth))
    cors.add(test_resource.add_route("POST", handler.verify_auth))
    cors.add(app.router.add_route("POST", "/authorize", handler.authorize))
    cors.add(app.router.add_route("GET", "/role", handler.get_role))
    cors.add(app.router.add_route("POST", "/signup", handler.signup))
    cors.add(app.router.add_route("POST", "/signout", handler.signout))
    cors.add(
        app.router.add_route("POST", "/update-password-no-auth", handler.update_password_no_auth)
    )
    cors.add(app.router.add_route("POST", "/update-password", handler.update_password))
    cors.add(app.router.add_route("POST", "/update-full-name", handler.update_full_name))
    cors.add(app.router.add_route("GET", "/ssh-keypair", handler.get_ssh_keypair))
    cors.add(app.router.add_route("PATCH", "/ssh-keypair", handler.generate_ssh_keypair))
    cors.add(app.router.add_route("POST", "/ssh-keypair", handler.upload_ssh_keypair))
    return app, [auth_middleware]
