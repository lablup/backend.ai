from __future__ import annotations

import functools
import hashlib
import hmac
import logging
import secrets
from contextlib import ExitStack
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final, Iterable, Mapping, Tuple
from urllib.parse import urlparse

import aiohttp_cors
import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc

from ai.backend.common import validators as tx
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.common.dto.manager.auth.field import (
    AuthResponseType,
    AuthSuccessResponse,
    AuthTokenType,
)
from ai.backend.common.exception import InvalidIpAddressValue
from ai.backend.common.plugin.hook import FIRST_COMPLETED, PASSED
from ai.backend.common.types import ReadableCIDR
from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.utils import with_log_context_fields
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

from ..errors.auth import AuthorizationFailed, InvalidAuthParameters
from ..errors.common import RejectedByHook
from ..models import keypair_resource_policies, keypairs, user_resource_policies, users
from ..models.utils import execute_with_retry
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params, get_handler_attr, set_handler_attr

if TYPE_CHECKING:
    from .context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

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


def _extract_auth_params(request):
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
        ret = params["signMethod"], access_key, signature
        return ret
    except (KeyError, ValueError):
        raise InvalidAuthParameters("Missing or malformed authorization parameters")


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
        assert mac_type == "hmac", "Unsupported request signing method (MAC type)"
        assert hash_type in hashlib.algorithms_guaranteed, (
            "Unsupported request signing method (hash type)"
        )

        new_api_version = request.headers.get("X-BackendAI-Version")
        legacy_api_version = request.headers.get("X-Sorna-Version")
        api_version = new_api_version or legacy_api_version
        assert api_version is not None, "API version missing in request headers"
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
    except ValueError:
        raise AuthorizationFailed("Invalid signature")
    except AssertionError as e:
        raise InvalidAuthParameters(e.args[0])


def validate_ip(request: web.Request, user: Mapping[str, Any]):
    allowed_client_ip = user.get("allowed_client_ip", None)
    if not allowed_client_ip or allowed_client_ip is None:
        # allowed_client_ip is None or [] - empty list
        return
    assert isinstance(allowed_client_ip, list)
    raw_client_addr: str | None = request.headers.get("X-Forwarded-For") or request.remote
    if raw_client_addr is None:
        raise AuthorizationFailed("Not allowed IP address")
    try:
        client_addr: ReadableCIDR = ReadableCIDR(raw_client_addr, is_network=False)
    except InvalidIpAddressValue:
        raise InvalidAuthParameters(f"{raw_client_addr} is invalid IP address value")
    if any(client_addr.address in allowed_ip_cand.address for allowed_ip_cand in allowed_client_ip):
        return
    raise AuthorizationFailed(f"'{client_addr}' is not allowed IP address")


@web.middleware
async def auth_middleware(request: web.Request, handler) -> web.StreamResponse:
    """
    Fetches user information and sets up keypair, user, and is_authorized
    attributes.
    """
    allow_list = request.app["auth_middleware_allowlist"]

    if any(request.path.startswith(path) for path in allow_list):
        request["is_authorized"] = False
        request["is_admin"] = False
        request["is_superadmin"] = False
        request["keypair"] = None
        request["user"] = None
        return await handler(request)

    # This is a global middleware: request.app is the root app.
    root_ctx: RootContext = request.app["_root.context"]
    request["is_authorized"] = False
    request["is_admin"] = False
    request["is_superadmin"] = False
    request["keypair"] = None
    request["user"] = None
    if not get_handler_attr(request, "auth_required", False):
        return await handler(request)
    if not check_date(request):
        raise InvalidAuthParameters("Date/time sync error")

    # PRE_AUTH_MIDDLEWARE allows authentication via 3rd-party request headers/cookies.
    # Any responsible hook must return a valid keypair.
    hook_result = await root_ctx.hook_plugin_ctx.dispatch(
        "PRE_AUTH_MIDDLEWARE",
        (request,),
        return_when=FIRST_COMPLETED,
    )
    user_row = None
    keypair_row = None

    async def _query_cred(access_key):
        async with root_ctx.db.begin_readonly() as conn:
            j = keypairs.join(
                keypair_resource_policies,
                keypairs.c.resource_policy == keypair_resource_policies.c.name,
            )
            query = (
                sa.select([keypairs, keypair_resource_policies], use_labels=True)
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
                sa.select([users, user_resource_policies], use_labels=True)
                .select_from(j)
                .where((keypairs.c.access_key == access_key))
            )
            result = await conn.execute(query)
            user_row = result.first()
            return user_row, keypair_row

    if hook_result.status != PASSED:
        raise RejectedByHook.from_hook_result(hook_result)
    elif hook_result.result:
        # Passed one of the hook.
        # The "None" access_key means that the hook has allowed anonymous access.
        access_key = hook_result.result
        if access_key is not None:
            user_row, keypair_row = await execute_with_retry(
                functools.partial(_query_cred, access_key)
            )
            if keypair_row is None:
                raise AuthorizationFailed("Access key not found")

            await root_ctx.valkey_stat.increment_keypair_query_count(access_key)
        else:
            # unsigned requests may be still accepted for public APIs
            pass
    else:
        # There were no hooks configured.
        # Perform our own authentication.
        params = _extract_auth_params(request)
        if params:
            sign_method, access_key, signature = params
            user_row, keypair_row = await execute_with_retry(
                functools.partial(_query_cred, access_key)
            )
            if keypair_row is None:
                raise AuthorizationFailed("Access key not found")
            my_signature = await sign_request(
                sign_method, request, keypair_row["keypairs_secret_key"]
            )
            if not secrets.compare_digest(my_signature, signature):
                raise AuthorizationFailed("Signature mismatch")
            await root_ctx.valkey_stat.increment_keypair_query_count(access_key)
        else:
            # unsigned requests may be still accepted for public APIs
            pass

    if user_row and keypair_row:
        auth_result = {
            "is_authorized": True,
            "keypair": {
                col.name: keypair_row[f"keypairs_{col.name}"]
                for col in keypairs.c
                if col.name != "secret_key"
            },
            "user": {
                col.name: user_row[f"users_{col.name}"]
                for col in users.c
                if col.name not in ("password", "description", "created_at")
            },
            "is_admin": keypair_row["keypairs_is_admin"],
        }

        validate_ip(request, auth_result["user"])
        auth_result["keypair"]["resource_policy"] = {
            col.name: keypair_row[f"keypair_resource_policies_{col.name}"]
            for col in keypair_resource_policies.c
        }
        auth_result["user"]["resource_policy"] = {
            col.name: user_row[f"user_resource_policies_{col.name}"]
            for col in user_resource_policies.c
        }
        auth_result["user"]["id"] = keypair_row["keypairs_user_id"]  # legacy
        auth_result["is_superadmin"] = auth_result["user"]["role"] == "superadmin"
        # Populate the result to the per-request state dict.
        request.update(auth_result)

    with ExitStack() as stack:
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
        # No matter if authenticated or not, pass-through to the handler.
        # (if it's required, `auth_required` decorator will handle the situation.)
        return await handler(request)


def auth_required(handler):
    @functools.wraps(handler)
    async def wrapped(request, *args, **kwargs):
        if request.get("is_authorized", False):
            return await handler(request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "user")
    return wrapped


def auth_required_for_method(method):
    @functools.wraps(method)
    async def wrapped(self, request, *args, **kwargs):
        if request.get("is_authorized", False):
            return await method(self, request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "user")
    return wrapped


def admin_required(handler):
    @functools.wraps(handler)
    async def wrapped(request, *args, **kwargs):
        if request.get("is_authorized", False) and request.get("is_admin", False):
            return await handler(request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "admin")
    return wrapped


def superadmin_required(handler):
    @functools.wraps(handler)
    async def wrapped(request, *args, **kwargs):
        if request.get("is_authorized", False) and request.get("is_superadmin", False):
            return await handler(request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "superadmin")
    return wrapped


@auth_required
@check_api_params(
    t.Dict({
        t.Key("echo"): t.String,
    })
)
async def test(request: web.Request, params: Any) -> web.Response:
    log.info("AUTH.TEST(ak:{})", request["keypair"]["access_key"])
    resp_data = {"authorized": "yes"}
    if "echo" in params:
        resp_data["echo"] = params["echo"]
    return web.json_response(resp_data)


@auth_required
@check_api_params(
    t.Dict({
        t.Key("group", default=None): t.Null | tx.UUID,
    })
)
async def get_role(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "AUTH.ROLES(ak:{}, d:{}, g:{})",
        request["keypair"]["access_key"],
        request["user"]["domain_name"],
        params["group"],
    )
    action = GetRoleAction(
        user_id=request["user"]["uuid"],
        group_id=params["group"],
        is_superadmin=request["is_superadmin"],
        is_admin=request["is_admin"],
    )
    result = await root_ctx.processors.auth.get_role.wait_for_complete(action)
    resp_data = {
        "global_role": result.global_role,
        "domain_role": result.domain_role,
        "group_role": result.group_role,
    }
    return web.json_response(resp_data)


@check_api_params(
    t.Dict({
        t.Key("type"): t.Enum("keypair", "jwt"),
        t.Key("domain"): t.String,
        t.Key("username"): t.String,
        t.Key("password"): t.String,
    }).allow_extra("*")
)
async def authorize(request: web.Request, params: Any) -> web.StreamResponse:
    log.info("AUTH.AUTHORIZE(d:{0[domain]}, u:{0[username]}, passwd:****, type:{0[type]})", params)
    root_ctx: RootContext = request.app["_root.context"]
    stoken = params.get("stoken") or params.get("sToken")
    action = AuthorizeAction(
        request=request,
        type=AuthTokenType(params["type"]),
        domain_name=params["domain"],
        email=params["username"],
        password=params["password"],
        stoken=stoken,
    )
    result = await root_ctx.processors.auth.authorize.wait_for_complete(action)

    if result.stream_response is not None:
        return result.stream_response

    assert result.authorization_result is not None
    auth_result = result.authorization_result
    data = AuthSuccessResponse(
        response_type=AuthResponseType.SUCCESS,
        access_key=auth_result.access_key,
        secret_key=auth_result.secret_key,
        role=auth_result.role,
        status=auth_result.status,
    )

    return web.json_response({
        "data": data.to_dict(),
    })


@check_api_params(
    t.Dict({
        t.Key("domain"): t.String,
        t.Key("email"): t.String,
        t.Key("password"): t.String,
    }).allow_extra("*")
)
async def signup(request: web.Request, params: Any) -> web.Response:
    log.info("AUTH.SIGNUP(d:{}, email:{}, passwd:****)", params["domain"], params["email"])
    root_ctx: RootContext = request.app["_root.context"]
    action = SignupAction(
        request=request,
        domain_name=params["domain"],
        email=params["email"],
        password=params["password"],
        username=params["username"] if "username" in params else None,
        full_name=params["full_name"] if "full_name" in params else None,
        description=params["description"] if "description" in params else None,
    )
    result = await root_ctx.processors.auth.signup.wait_for_complete(action)

    resp_data = {
        "access_key": result.access_key,
        "secret_key": result.secret_key,
    }

    return web.json_response(resp_data, status=HTTPStatus.CREATED)


@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["email", "username"]): t.String,
        t.Key("password"): t.String,
    })
)
async def signout(request: web.Request, params: Any) -> web.Response:
    domain_name = request["user"]["domain_name"]
    email = params["email"]
    password = params["password"]
    log.info("AUTH.SIGNOUT(d:{}, email:{})", domain_name, email)
    root_ctx: RootContext = request.app["_root.context"]

    await root_ctx.processors.auth.signout.wait_for_complete(
        SignoutAction(
            user_id=request["user"]["uuid"],
            domain_name=domain_name,
            requester_email=request["user"]["email"],
            email=email,
            password=password,
        )
    )

    return web.json_response({})


@auth_required
@check_api_params(
    t.Dict({
        t.Key("email"): t.String,
        t.Key("full_name"): t.String,
    })
)
async def update_full_name(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    domain_name = request["user"]["domain_name"]
    email = request["user"]["email"]
    log.info("AUTH.UPDATE_FULL_NAME(d:{}, email:{})", domain_name, email)
    result = await root_ctx.processors.auth.update_full_name.wait_for_complete(
        UpdateFullNameAction(
            user_id=request["user"]["uuid"],
            full_name=params["full_name"],
            domain_name=domain_name,
            email=email,
        )
    )

    if not result.success:
        log.info("AUTH.UPDATE_FULL_NAME(d:{}, email:{}): Unknown user", domain_name, email)
        return web.json_response({"error_msg": "Unknown user"}, status=HTTPStatus.BAD_REQUEST)

    return web.json_response({}, status=HTTPStatus.OK)


@auth_required
@check_api_params(
    t.Dict({
        t.Key("old_password"): t.String,
        t.Key("new_password"): t.String,
        t.Key("new_password2"): t.String,
    })
)
async def update_password(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    domain_name = request["user"]["domain_name"]
    email = request["user"]["email"]
    log.info("AUTH.UPDATE_PASSWORD(d:{}, email:{})", domain_name, email)

    action = UpdatePasswordAction(
        request=request,
        user_id=request["user"]["uuid"],
        domain_name=domain_name,
        email=email,
        old_password=params["old_password"],
        new_password=params["new_password"],
        new_password_confirm=params["new_password2"],
    )
    result = await root_ctx.processors.auth.update_password.wait_for_complete(action)
    if not result.success:
        return web.json_response(
            {"error_msg": "new password mismatch"}, status=HTTPStatus.BAD_REQUEST
        )
    return web.json_response({}, status=HTTPStatus.OK)


@check_api_params(
    t.Dict({
        t.Key("domain"): t.String,
        t.Key("username"): t.String,
        t.Key("current_password"): t.String,
        t.Key("new_password"): t.String,
    })
)
async def update_password_no_auth(request: web.Request, params: Any) -> web.Response:
    """
    Update user's password without any authorization
    to allows users to update passwords that have expired
    because it's been too long since a user changed the password.
    """

    root_ctx: RootContext = request.app["_root.context"]
    log.info(
        "AUTH.UPDATE_PASSWORD_NO_AUTH(d:{}, u:{}, passwd:****)",
        params["domain"],
        params["username"],
    )

    action = UpdatePasswordNoAuthAction(
        request=request,
        domain_name=params["domain"],
        email=params["username"],
        current_password=params["current_password"],
        new_password=params["new_password"],
    )
    result = await root_ctx.processors.auth.update_password_no_auth.wait_for_complete(action)
    return web.json_response(
        {"password_changed_at": result.password_changed_at.isoformat()}, status=HTTPStatus.CREATED
    )


@auth_required
async def get_ssh_keypair(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    domain_name = request["user"]["domain_name"]
    access_key = request["keypair"]["access_key"]
    log.info("AUTH.GET_SSH_KEYPAIR(d:{}, ak:{})", domain_name, access_key)
    result = await root_ctx.processors.auth.get_ssh_keypair.wait_for_complete(
        GetSSHKeypairAction(
            user_id=request["user"]["uuid"],
            access_key=access_key,
        )
    )
    return web.json_response({"ssh_public_key": result.public_key}, status=HTTPStatus.OK)


@auth_required
async def generate_ssh_keypair(request: web.Request) -> web.Response:
    domain_name = request["user"]["domain_name"]
    access_key = request["keypair"]["access_key"]
    log.info("AUTH.REFRESH_SSH_KEYPAIR(d:{}, ak:{})", domain_name, access_key)
    root_ctx: RootContext = request.app["_root.context"]
    result = await root_ctx.processors.auth.generate_ssh_keypair.wait_for_complete(
        GenerateSSHKeypairAction(
            user_id=request["user"]["uuid"],
            access_key=access_key,
        )
    )
    data = {
        "ssh_public_key": result.ssh_keypair.ssh_public_key,
        "ssh_private_key": result.ssh_keypair.ssh_private_key,
    }
    return web.json_response(data, status=HTTPStatus.OK)


@auth_required
@check_api_params(
    t.Dict({
        t.Key("pubkey"): t.String,
        t.Key("privkey"): t.String,
    })
)
async def upload_ssh_keypair(request: web.Request, params: Any) -> web.Response:
    domain_name = request["user"]["domain_name"]
    access_key = request["keypair"]["access_key"]
    pubkey = f"{params['pubkey'].rstrip()}\n"
    privkey = f"{params['privkey'].rstrip()}\n"
    log.info("AUTH.SAVE_SSH_KEYPAIR(d:{}, ak:{})", domain_name, access_key)
    root_ctx: RootContext = request.app["_root.context"]

    result = await root_ctx.processors.auth.upload_ssh_keypair.wait_for_complete(
        UploadSSHKeypairAction(
            user_id=request["user"]["uuid"],
            public_key=pubkey,
            private_key=privkey,
            access_key=access_key,
        )
    )
    data = {
        "ssh_public_key": result.ssh_keypair.ssh_public_key,
        "ssh_private_key": result.ssh_keypair.ssh_private_key,
    }
    return web.json_response(data, status=HTTPStatus.OK)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "auth"  # slashed to distinguish with "/vN/authorize"
    app["api_versions"] = (1, 2, 3, 4)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", test))
    cors.add(root_resource.add_route("POST", test))
    test_resource = cors.add(app.router.add_resource("/test"))
    cors.add(test_resource.add_route("GET", test))
    cors.add(test_resource.add_route("POST", test))
    cors.add(app.router.add_route("POST", "/authorize", authorize))
    cors.add(app.router.add_route("GET", "/role", get_role))
    cors.add(app.router.add_route("POST", "/signup", signup))
    cors.add(app.router.add_route("POST", "/signout", signout))
    cors.add(app.router.add_route("POST", "/update-password-no-auth", update_password_no_auth))
    cors.add(app.router.add_route("POST", "/update-password", update_password))
    cors.add(app.router.add_route("POST", "/update-full-name", update_full_name))
    cors.add(app.router.add_route("GET", "/ssh-keypair", get_ssh_keypair))
    cors.add(app.router.add_route("PATCH", "/ssh-keypair", generate_ssh_keypair))
    cors.add(app.router.add_route("POST", "/ssh-keypair", upload_ssh_keypair))
    return app, [auth_middleware]
