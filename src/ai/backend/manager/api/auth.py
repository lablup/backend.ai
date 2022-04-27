from collections import ChainMap
from datetime import datetime, timedelta
import functools
import hashlib, hmac
import logging
import secrets
from typing import (
    Any,
    Final,
    Iterable,
    Mapping,
    TYPE_CHECKING,
    Tuple,
    cast,
)

from aiohttp import web
import aiohttp_cors
from aioredis import Redis
from aioredis.client import Pipeline as RedisPipeline
from dateutil.tz import tzutc
from dateutil.parser import parse as dtparse
import sqlalchemy as sa
import trafaret as t

from ai.backend.common import redis, validators as tx
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin.hook import (
    ALL_COMPLETED,
    FIRST_COMPLETED,
    PASSED,
)

from ..models import (
    keypairs, keypair_resource_policies, users,
)
from ..models.user import UserRole, UserStatus, INACTIVE_USER_STATUSES, check_credential
from ..models.keypair import generate_keypair as _gen_keypair, generate_ssh_keypair
from ..models.group import association_groups_users, groups
from ..models.utils import execute_with_retry
from .exceptions import (
    AuthorizationFailed,
    GenericBadRequest,
    GenericForbidden,
    ObjectNotFound,
    InternalServerError,
    InvalidAuthParameters,
    InvalidAPIParameters,
    RejectedByHook,
)
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params, set_handler_attr, get_handler_attr

if TYPE_CHECKING:
    from .context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__name__))

whois_timezone_info: Final = {
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


def _extract_auth_params(request):
    """
    HTTP Authorization header must be formatted as:
    "Authorization: BackendAI signMethod=HMAC-SHA256,
                    credential=<ACCESS_KEY>:<SIGNATURE>"
    """
    auth_hdr = request.headers.get('Authorization')
    if not auth_hdr:
        return None
    pieces = auth_hdr.split(' ', 1)
    if len(pieces) != 2:
        raise InvalidAuthParameters('Malformed authorization header')
    auth_type, auth_str = pieces
    if auth_type not in ('BackendAI', 'Sorna'):
        raise InvalidAuthParameters('Invalid authorization type name')

    raw_params = map(lambda s: s.strip(), auth_str.split(','))
    params = {}
    for param in raw_params:
        key, value = param.split('=', 1)
        params[key.strip()] = value.strip()

    try:
        access_key, signature = params['credential'].split(':', 1)
        ret = params['signMethod'], access_key, signature
        return ret
    except (KeyError, ValueError):
        raise InvalidAuthParameters('Missing or malformed authorization parameters')


def check_date(request: web.Request) -> bool:
    raw_date = request.headers.get('Date')
    if not raw_date:
        raw_date = request.headers.get('X-BackendAI-Date',
                                       request.headers.get('X-Sorna-Date'))
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
        request['date'] = date
        request['raw_date'] = raw_date
        if not (min_date < date < max_date):
            return False
    except ValueError:
        return False
    return True


async def sign_request(sign_method: str, request: web.Request, secret_key: str) -> str:
    try:
        mac_type, hash_type = map(lambda s: s.lower(), sign_method.split('-'))
        assert mac_type == 'hmac', 'Unsupported request signing method (MAC type)'
        assert hash_type in hashlib.algorithms_guaranteed, \
               'Unsupported request signing method (hash type)'

        new_api_version = request.headers.get('X-BackendAI-Version')
        legacy_api_version = request.headers.get('X-Sorna-Version')
        api_version = new_api_version or legacy_api_version
        assert api_version is not None, 'API version missing in request headers'
        body = b''
        if api_version < 'v4.20181215':
            if (request.can_read_body and
                request.content_type != 'multipart/form-data'):
                # read the whole body if neither streaming nor bodyless
                body = await request.read()
        body_hash = hashlib.new(hash_type, body).hexdigest()

        sign_bytes = ('{0}\n{1}\n{2}\nhost:{3}\ncontent-type:{4}\n'
                      'x-{name}-version:{5}\n{6}').format(
            request.method, str(request.raw_path), request['raw_date'],
            request.host, request.content_type, api_version,
            body_hash,
            name='backendai' if new_api_version is not None else 'sorna',
        ).encode()
        sign_key = hmac.new(secret_key.encode(),
                            request['date'].strftime('%Y%m%d').encode(),
                            hash_type).digest()
        sign_key = hmac.new(sign_key, request.host.encode(), hash_type).digest()
        return hmac.new(sign_key, sign_bytes, hash_type).hexdigest()
    except ValueError:
        raise AuthorizationFailed('Invalid signature')
    except AssertionError as e:
        raise InvalidAuthParameters(e.args[0])


@web.middleware
async def auth_middleware(request: web.Request, handler) -> web.StreamResponse:
    """
    Fetches user information and sets up keypair, uesr, and is_authorized
    attributes.
    """
    # This is a global middleware: request.app is the root app.
    root_ctx: RootContext = request.app['_root.context']
    request['is_authorized'] = False
    request['is_admin'] = False
    request['is_superadmin'] = False
    request['keypair'] = None
    request['user'] = None
    if not get_handler_attr(request, 'auth_required', False):
        return (await handler(request))
    if not check_date(request):
        raise InvalidAuthParameters('Date/time sync error')

    # PRE_AUTH_MIDDLEWARE allows authentication via 3rd-party request headers/cookies.
    # Any responsible hook must return a valid keypair.
    hook_result = await root_ctx.hook_plugin_ctx.dispatch(
        'PRE_AUTH_MIDDLEWARE',
        (request,),
        return_when=FIRST_COMPLETED,
    )
    row = None
    if hook_result.status != PASSED:
        raise RejectedByHook.from_hook_result(hook_result)
    elif hook_result.result:
        # Passed one of the hook.
        # The "None" access_key means that the hook has allowed anonymous access.
        access_key = hook_result.result
        if access_key is not None:
            async def _query_cred():
                async with root_ctx.db.begin_readonly() as conn:
                    j = (
                        keypairs
                        .join(users, keypairs.c.user == users.c.uuid)
                        .join(
                            keypair_resource_policies,
                            keypairs.c.resource_policy == keypair_resource_policies.c.name,
                        )
                    )
                    query = (
                        sa.select([users, keypairs, keypair_resource_policies], use_labels=True)
                        .select_from(j)
                        .where(
                            (keypairs.c.access_key == access_key) &
                            (keypairs.c.is_active.is_(True)),
                        )
                    )
                    result = await conn.execute(query)
                return result.first()

            row = await execute_with_retry(_query_cred)
            if row is None:
                raise AuthorizationFailed('Access key not found')

            async def _pipe_builder(r: Redis) -> RedisPipeline:
                pipe = r.pipeline()
                num_queries_key = f'kp:{access_key}:num_queries'
                pipe.incr(num_queries_key)
                pipe.expire(num_queries_key, 86400 * 30)  # retention: 1 month
                return pipe

            await redis.execute(root_ctx.redis_stat, _pipe_builder)
        else:
            # unsigned requests may be still accepted for public APIs
            pass
    else:
        # There were no hooks configured.
        # Perform our own authentication.
        params = _extract_auth_params(request)
        if params:
            sign_method, access_key, signature = params

            async def _query_cred():
                async with root_ctx.db.begin_readonly() as conn:
                    j = (
                        keypairs
                        .join(users, keypairs.c.user == users.c.uuid)
                        .join(keypair_resource_policies,
                              keypairs.c.resource_policy == keypair_resource_policies.c.name)
                    )
                    query = (
                        sa.select([users, keypairs, keypair_resource_policies], use_labels=True)
                        .select_from(j)
                        .where(
                            (keypairs.c.access_key == access_key) &
                            (keypairs.c.is_active.is_(True)),
                        )
                    )
                    result = await conn.execute(query)
                    return result.first()

            row = await execute_with_retry(_query_cred)
            if row is None:
                raise AuthorizationFailed('Access key not found')
            my_signature = \
                await sign_request(sign_method, request, row['keypairs_secret_key'])
            if not secrets.compare_digest(my_signature, signature):
                raise AuthorizationFailed('Signature mismatch')

            async def _pipe_builder(r: Redis) -> RedisPipeline:
                pipe = r.pipeline()
                num_queries_key = f'kp:{access_key}:num_queries'
                pipe.incr(num_queries_key)
                pipe.expire(num_queries_key, 86400 * 30)  # retention: 1 month
                return pipe

            await redis.execute(root_ctx.redis_stat, _pipe_builder)
        else:
            # unsigned requests may be still accepted for public APIs
            pass

    if row is not None:
        auth_result = {
            'is_authorized': True,
            'keypair': {
                col.name: row[f'keypairs_{col.name}']
                for col in keypairs.c
                if col.name != 'secret_key'
            },
            'user': {
                col.name: row[f'users_{col.name}']
                for col in users.c
                if col.name not in ('password', 'description', 'created_at')
            },
            'is_admin': row['keypairs_is_admin'],
        }
        auth_result['keypair']['resource_policy'] = {
            col.name: row[f'keypair_resource_policies_{col.name}']
            for col in keypair_resource_policies.c
        }
        auth_result['user']['id'] = row['keypairs_user_id']  # legacy
        auth_result['is_superadmin'] = (auth_result['user']['role'] == 'superadmin')
        # Populate the result to the per-request state dict.
        request.update(auth_result)

    # No matter if authenticated or not, pass-through to the handler.
    # (if it's required, auth_required decorator will handle the situation.)
    return (await handler(request))


def auth_required(handler):

    @functools.wraps(handler)
    async def wrapped(request, *args, **kwargs):
        if request.get('is_authorized', False):
            return (await handler(request, *args, **kwargs))
        raise AuthorizationFailed('Unauthorized access')

    set_handler_attr(wrapped, 'auth_required', True)
    return wrapped


def admin_required(handler):

    @functools.wraps(handler)
    async def wrapped(request, *args, **kwargs):
        if request.get('is_authorized', False) and request.get('is_admin', False):
            return (await handler(request, *args, **kwargs))
        raise AuthorizationFailed('Unauthorized access')

    set_handler_attr(wrapped, 'auth_required', True)
    return wrapped


def superadmin_required(handler):

    @functools.wraps(handler)
    async def wrapped(request, *args, **kwargs):
        if request.get('is_authorized', False) and request.get('is_superadmin', False):
            return (await handler(request, *args, **kwargs))
        raise AuthorizationFailed('Unauthorized access')

    set_handler_attr(wrapped, 'auth_required', True)
    return wrapped


@auth_required
@check_api_params(
    t.Dict({
        t.Key('echo'): t.String,
    }))
async def test(request: web.Request, params: Any) -> web.Response:
    log.info('AUTH.TEST(ak:{})', request['keypair']['access_key'])
    resp_data = {'authorized': 'yes'}
    if 'echo' in params:
        resp_data['echo'] = params['echo']
    return web.json_response(resp_data)


@auth_required
@check_api_params(
    t.Dict({
        t.Key('group', default=None): t.Null | tx.UUID,
    }))
async def get_role(request: web.Request, params: Any) -> web.Response:
    group_role = None
    root_ctx: RootContext = request.app['_root.context']
    log.info(
        'AUTH.ROLES(ak:{}, d:{}, g:{})',
        request['keypair']['access_key'],
        request['user']['domain_name'],
        params['group'],
    )
    if params['group'] is not None:
        query = (
            # TODO: per-group role is not yet implemented.
            sa.select([association_groups_users.c.group_id])
            .select_from(association_groups_users)
            .where(
                (association_groups_users.c.group_id == params['group']) &
                (association_groups_users.c.user_id == request['user']['uuid']),
            )
        )
        async with root_ctx.db.begin() as conn:
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise ObjectNotFound(
                    extra_msg='No such project or you are not the member of it.',
                    object_name='project (user group)',
                )
        group_role = 'user'
    resp_data = {
        'global_role': 'superadmin' if request['is_superadmin'] else 'user',
        'domain_role': 'admin' if request['is_admin'] else 'user',
        'group_role': group_role,
    }
    return web.json_response(resp_data)


@check_api_params(
    t.Dict({
        t.Key('type'): t.Enum('keypair', 'jwt'),
        t.Key('domain'): t.String,
        t.Key('username'): t.String,
        t.Key('password'): t.String,
    }))
async def authorize(request: web.Request, params: Any) -> web.Response:
    if params['type'] != 'keypair':
        # other types are not implemented yet.
        raise InvalidAPIParameters('Unsupported authorization type')
    log.info('AUTH.AUTHORIZE(d:{0[domain]}, u:{0[username]}, passwd:****, type:{0[type]})', params)
    root_ctx: RootContext = request.app['_root.context']

    # [Hooking point for AUTHORIZE with the FIRST_COMPLETED requirement]
    # The hook handlers should accept the whole ``params`` dict, and optional
    # ``db`` parameter (if the hook needs to query to database).
    # They should return a corresponding Backend.AI user object after performing
    # their own authentication steps, like LDAP authentication, etc.
    hook_result = await root_ctx.hook_plugin_ctx.dispatch(
        'AUTHORIZE',
        (request, params),
        return_when=FIRST_COMPLETED,
    )
    if hook_result.status != PASSED:
        raise RejectedByHook.from_hook_result(hook_result)
    elif hook_result.result:
        # Passed one of AUTHORIZED hook
        user = hook_result.result
    else:
        # No AUTHORIZE hook is defined (proceed with normal login)
        user = await check_credential(
            root_ctx.db,
            params['domain'], params['username'], params['password'],
        )
    if user is None:
        raise AuthorizationFailed('User credential mismatch.')
    if user['status'] == UserStatus.BEFORE_VERIFICATION:
        raise AuthorizationFailed('This account needs email verification.')
    if user['status'] in INACTIVE_USER_STATUSES:
        raise AuthorizationFailed('User credential mismatch.')
    async with root_ctx.db.begin() as conn:
        query = (sa.select([keypairs.c.access_key, keypairs.c.secret_key])
                   .select_from(keypairs)
                   .where(
                       (keypairs.c.user == user['uuid']) &
                       (keypairs.c.is_active),
                   )
                   .order_by(sa.desc(keypairs.c.is_admin)))
        result = await conn.execute(query)
        keypair = result.first()
    if keypair is None:
        raise AuthorizationFailed('No API keypairs found.')
    # [Hooking point for POST_AUTHORIZE as one-way notification]
    # The hook handlers should accept a tuple of the request, user, and keypair objects.
    await root_ctx.hook_plugin_ctx.notify(
        'POST_AUTHORIZE',
        (request, user, keypair),
    )
    return web.json_response({
        'data': {
            'access_key': keypair['access_key'],
            'secret_key': keypair['secret_key'],
            'role': user['role'],
            'status': user['status'],
        },
    })


@check_api_params(
    t.Dict({
        t.Key('domain'): t.String,
        t.Key('email'): t.String,
        t.Key('password'): t.String,
    }).allow_extra('*'))
async def signup(request: web.Request, params: Any) -> web.Response:
    log_fmt = 'AUTH.SIGNUP(d:{}, email:{}, passwd:****)'
    log_args = (params['domain'], params['email'])
    log.info(log_fmt, *log_args)
    root_ctx: RootContext = request.app['_root.context']

    # [Hooking point for PRE_SIGNUP with the ALL_COMPLETED requirement]
    # The hook handlers should accept the whole ``params`` dict.
    # They should return a dict to override the user information,
    # where the keys must be a valid field name of the users table,
    # with two exceptions: "resource_policy" (name) and "group" (name).
    # A plugin may return an empty dict if it has nothing to override.
    hook_result = await root_ctx.hook_plugin_ctx.dispatch(
        'PRE_SIGNUP',
        (params, ),
        return_when=ALL_COMPLETED,
    )
    if hook_result.status != PASSED:
        raise RejectedByHook.from_hook_result(hook_result)
    else:
        # Merge the hook results as a single map.
        user_data_overriden = ChainMap(*cast(Mapping, hook_result.result))

    async with root_ctx.db.begin() as conn:
        # Check if email already exists.
        query = (sa.select([users])
                   .select_from(users)
                   .where((users.c.email == params['email'])))
        result = await conn.execute(query)
        row = result.first()
        if row is not None:
            raise GenericBadRequest('Email already exists')

        # Create a user.
        data = {
            'domain_name': params['domain'],
            'username': params['username'] if 'username' in params else params['email'],
            'email': params['email'],
            'password': params['password'],
            'need_password_change': False,
            'full_name': params['full_name'] if 'full_name' in params else '',
            'description': params['description'] if 'description' in params else '',
            'status': UserStatus.ACTIVE,
            'status_info': 'user-signup',
            'role': UserRole.USER,
            'integration_id': None,
        }
        if user_data_overriden:
            for key, val in user_data_overriden.items():
                if key in data:  # take only valid fields
                    data[key] = val
        query = (users.insert().values(data))
        result = await conn.execute(query)
        if result.rowcount > 0:
            checkq = users.select().where(users.c.email == params['email'])
            result = await conn.execute(checkq)
            user = result.first()
            # Create user's first access_key and secret_key.
            ak, sk = _gen_keypair()
            resource_policy = (
                user_data_overriden.get('resource_policy', 'default')
            )
            kp_data = {
                'user_id': params['email'],
                'access_key': ak,
                'secret_key': sk,
                'is_active': True if data.get('status') == UserStatus.ACTIVE else False,
                'is_admin': False,
                'resource_policy': resource_policy,
                'rate_limit': 1000,
                'num_queries': 0,
                'user': user.uuid,
            }
            query = (keypairs.insert().values(kp_data))
            await conn.execute(query)

            # Add user to the default group.
            group_name = user_data_overriden.get('group', 'default')
            query = (sa.select([groups.c.id])
                       .select_from(groups)
                       .where(groups.c.domain_name == params['domain'])
                       .where(groups.c.name == group_name))
            result = await conn.execute(query)
            grp = result.first()
            if grp is not None:
                values = [{'user_id': user.uuid, 'group_id': grp.id}]
                query = association_groups_users.insert().values(values)
                await conn.execute(query)
        else:
            raise InternalServerError('Error creating user account')

    resp_data = {
        'access_key': ak,
        'secret_key': sk,
    }

    # [Hooking point for POST_SIGNUP as one-way notification]
    # The hook handlers should accept a tuple of the user email,
    # the new user's UUID, and a dict with initial user's preferences.
    initial_user_prefs = {
        'lang': request.headers.get('Accept-Language', 'en-us').split(',')[0].lower(),
    }
    await root_ctx.hook_plugin_ctx.notify(
        'POST_SIGNUP',
        (params['email'], user.uuid, initial_user_prefs),
    )
    return web.json_response(resp_data, status=201)


@auth_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(['email', 'username']): t.String,
        t.Key('password'): t.String,
    }))
async def signout(request: web.Request, params: Any) -> web.Response:
    domain_name = request['user']['domain_name']
    log.info('AUTH.SIGNOUT(d:{}, email:{})', domain_name, params['email'])
    root_ctx: RootContext = request.app['_root.context']
    if request['user']['email'] != params['email']:
        raise GenericForbidden('Not the account owner')
    result = await check_credential(
        root_ctx.db,
        domain_name, params['email'], params['password'])
    if result is None:
        raise GenericBadRequest('Invalid email and/or password')
    async with root_ctx.db.begin() as conn:
        # Inactivate the user.
        query = (
            users.update()
            .values(status=UserStatus.INACTIVE)
            .where(users.c.email == params['email'])
        )
        await conn.execute(query)
        # Inactivate every keypairs of the user.
        query = (
            keypairs.update()
            .values(is_active=False)
            .where(keypairs.c.user_id == params['email'])
        )
        await conn.execute(query)
    return web.json_response({})


@auth_required
@check_api_params(
    t.Dict({
        t.Key('email'): t.String,
        t.Key('full_name'): t.String,
    }))
async def update_full_name(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    domain_name = request['user']['domain_name']
    email = request['user']['email']
    log_fmt = 'AUTH.UPDATE_FULL_NAME(d:{}, email:{})'
    log_args = (domain_name, email)
    log.info(log_fmt, *log_args)
    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([users])
            .select_from(users)
            .where(
                (users.c.email == email) &
                (users.c.domain_name == domain_name),
            )
        )
        result = await conn.execute(query)
        user = result.first()
        if user is None:
            log.info(log_fmt + ': Unknown user', *log_args)
            return web.json_response({'error_msg': 'Unknown user'}, status=400)

        # If user is not null, then it updates user full_name.
        data = {
            'full_name': params['full_name'],
        }
        update_query = (users.update().values(data).where(users.c.email == email))
        await conn.execute(update_query)
    return web.json_response({}, status=200)


@auth_required
@check_api_params(
    t.Dict({
        t.Key('old_password'): t.String,
        t.Key('new_password'): t.String,
        t.Key('new_password2'): t.String,
    }))
async def update_password(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    domain_name = request['user']['domain_name']
    email = request['user']['email']
    log_fmt = 'AUTH.UDPATE_PASSWORD(d:{}, email:{})'
    log_args = (domain_name, email)
    log.info(log_fmt, *log_args)

    user = await check_credential(root_ctx.db, domain_name, email, params['old_password'])
    if user is None:
        log.info(log_fmt + ': old password mismtach', *log_args)
        raise AuthorizationFailed('Old password mismatch')
    if params['new_password'] != params['new_password2']:
        log.info(log_fmt + ': new password mismtach', *log_args)
        return web.json_response({'error_msg': 'new password mismitch'}, status=400)

    # [Hooking point for VERIFY_PASSWORD_FORMAT with the ALL_COMPLETED requirement]
    # The hook handlers should accept the old password and the new password and implement their
    # own password validation rules.
    # They should return None if the validation is successful and raise the Reject error
    # otherwise.
    hook_result = await root_ctx.hook_plugin_ctx.dispatch(
        'VERIFY_PASSWORD_FORMAT',
        (params['old_password'], params['new_password']),
        return_when=ALL_COMPLETED,
    )
    if hook_result.status != PASSED:
        hook_result.reason = hook_result.reason or 'invalid password format'
        raise RejectedByHook.from_hook_result(hook_result)

    async with root_ctx.db.begin() as conn:
        # Update user password.
        data = {
            'password': params['new_password'],
            'need_password_change': False,
        }
        query = (users.update().values(data).where(users.c.email == email))
        await conn.execute(query)
    return web.json_response({}, status=200)


@auth_required
async def get_ssh_keypair(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    domain_name = request['user']['domain_name']
    access_key = request['keypair']['access_key']
    log_fmt = 'AUTH.GET_SSH_KEYPAIR(d:{}, ak:{})'
    log_args = (domain_name, access_key)
    log.info(log_fmt, *log_args)
    async with root_ctx.db.begin() as conn:
        # Get SSH public key. Return partial string from the public key just for checking.
        query = (
            sa.select([keypairs.c.ssh_public_key])
            .where(keypairs.c.access_key == access_key)
        )
        pubkey = await conn.scalar(query)
    return web.json_response({'ssh_public_key': pubkey}, status=200)


@auth_required
async def refresh_ssh_keypair(request: web.Request) -> web.Response:
    domain_name = request['user']['domain_name']
    access_key = request['keypair']['access_key']
    log_fmt = 'AUTH.REFRESH_SSH_KEYPAIR(d:{}, ak:{})'
    log_args = (domain_name, access_key)
    log.info(log_fmt, *log_args)
    root_ctx: RootContext = request.app['_root.context']
    async with root_ctx.db.begin() as conn:
        pubkey, privkey = generate_ssh_keypair()
        data = {
            'ssh_public_key': pubkey,
            'ssh_private_key': privkey,
        }
        query = (
            keypairs.update()
            .values(data)
            .where(keypairs.c.access_key == access_key)
        )
        await conn.execute(query)
    return web.json_response(data, status=200)


def create_app(default_cors_options: CORSOptions) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app['prefix'] = 'auth'  # slashed to distinguish with "/vN/authorize"
    app['api_versions'] = (1, 2, 3, 4)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r''))
    cors.add(root_resource.add_route('GET', test))
    cors.add(root_resource.add_route('POST', test))
    test_resource = cors.add(app.router.add_resource('/test'))
    cors.add(test_resource.add_route('GET', test))
    cors.add(test_resource.add_route('POST', test))
    cors.add(app.router.add_route('POST', '/authorize', authorize))
    cors.add(app.router.add_route('GET', '/role', get_role))
    cors.add(app.router.add_route('POST', '/signup', signup))
    cors.add(app.router.add_route('POST', '/signout', signout))
    cors.add(app.router.add_route('POST', '/update-password', update_password))
    cors.add(app.router.add_route('POST', '/update-full-name', update_full_name))
    cors.add(app.router.add_route('GET', '/ssh-keypair', get_ssh_keypair))
    cors.add(app.router.add_route('PATCH', '/ssh-keypair', refresh_ssh_keypair))
    return app, [auth_middleware]
