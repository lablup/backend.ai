import asyncio
from collections import defaultdict
import functools
import io
import inspect
import itertools
import json
import logging
import numbers
import re
import time
import traceback
from typing import (
    Any,
    Awaitable,
    Callable,
    Hashable,
    Mapping,
    MutableMapping,
    Optional, TYPE_CHECKING,
    Tuple,
    Union,
)
import uuid

from aiohttp import web
import trafaret as t
import sqlalchemy as sa
import yaml

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AccessKey

from ..models import keypairs, users, UserRole
from .exceptions import InvalidAPIParameters, GenericForbidden, QueryNotImplemented

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))

_rx_sitepkg_path = re.compile(r'^.+/site-packages/')


def method_placeholder(orig_method):
    async def _handler(request):
        raise web.HTTPMethodNotAllowed(request.method, [orig_method])

    return _handler


async def get_access_key_scopes(request: web.Request, params: Any = None) -> Tuple[AccessKey, AccessKey]:
    if not request['is_authorized']:
        raise GenericForbidden('Only authorized requests may have access key scopes.')
    root_ctx: RootContext = request.app['_root.context']
    requester_access_key: AccessKey = request['keypair']['access_key']
    if (
        params is not None and
        (owner_access_key := params.get('owner_access_key', None)) is not None and
        owner_access_key != requester_access_key
    ):
        async with root_ctx.db.begin_readonly() as conn:
            query = (
                sa.select([users.c.domain_name, users.c.role])
                .select_from(
                    sa.join(keypairs, users,
                            keypairs.c.user == users.c.uuid))
                .where(keypairs.c.access_key == owner_access_key)
            )
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise InvalidAPIParameters("Unknown owner access key")
            owner_domain = row['domain_name']
            owner_role = row['role']
        if request['is_superadmin']:
            pass
        elif request['is_admin']:
            if request['user']['domain_name'] != owner_domain:
                raise GenericForbidden(
                    "Domain-admins can perform operations on behalf of "
                    "other users in the same domain only.",
                )
            if owner_role == UserRole.SUPERADMIN:
                raise GenericForbidden(
                    "Domain-admins cannot perform operations on behalf of super-admins.",
                )
            pass
        else:
            raise GenericForbidden(
                "Only admins can perform operations on behalf of other users.",
            )
        return requester_access_key, owner_access_key
    return requester_access_key, requester_access_key


async def get_user_scopes(
    request: web.Request,
    params: Optional[dict[str, Any]] = None,
) -> tuple[uuid.UUID, UserRole]:
    root_ctx: RootContext = request.app['_root.context']
    if not request['is_authorized']:
        raise GenericForbidden("Only authorized requests may have user scopes.")
    if (
        params is not None and
        (owner_user_email := params.get('owner_user_email')) is not None
    ):
        if not request['is_superadmin']:
            raise InvalidAPIParameters("Only superadmins may have user scopes.")
        async with root_ctx.db.begin_readonly() as conn:
            user_query = (
                sa.select([users.c.uuid, users.c.role, users.c.domain_name])
                .select_from(users)
                .where(
                    (users.c.email == owner_user_email),
                )
            )
            result = await conn.execute(user_query)
            row = result.first()
            if row is None:
                raise InvalidAPIParameters("Cannot delegate an unknown user")
            owner_user_uuid = row['uuid']
            owner_user_role = row['role']
            owner_user_domain = row['domain_name']
        if request['is_superadmin']:
            pass
        elif request['is_admin']:
            if request['user']['domain_name'] != owner_user_domain:
                raise GenericForbidden(
                    "Domain-admins can perform operations on behalf of "
                    "other users in the same domain only.",
                )
            if owner_user_role == UserRole.SUPERADMIN:
                raise GenericForbidden(
                    "Domain-admins cannot perform operations on behalf of super-admins.",
                )
            pass
        else:
            raise GenericForbidden(
                "Only admins can perform operations on behalf of other users.",
            )
    else:
        owner_user_uuid = request['user']['uuid']
        owner_user_role = request['user']['role']
    return owner_user_uuid, owner_user_role


def check_api_params(
    checker: t.Trafaret,
    loads: Callable[[str], Any] = None,
    query_param_checker: t.Trafaret = None,
) -> Any:
    # FIXME: replace ... with [web.Request, Any...] in the future mypy
    def wrap(handler: Callable[..., Awaitable[web.Response]]):

        @functools.wraps(handler)
        async def wrapped(request: web.Request, *args, **kwargs) -> web.Response:
            orig_params: Any
            body: str = ''
            try:
                body_exists = request.can_read_body
                if body_exists:
                    body = await request.text()
                    if request.content_type == 'text/yaml':
                        orig_params = yaml.load(body, Loader=yaml.BaseLoader)
                    else:
                        orig_params = (loads or json.loads)(body)
                else:
                    orig_params = dict(request.query)
                stripped_params = orig_params.copy()
                log.debug('stripped raw params: {}', mask_sensitive_keys(stripped_params))
                checked_params = checker.check(stripped_params)
                if body_exists and query_param_checker:
                    query_params = query_param_checker.check(request.query)
                    kwargs['query'] = query_params
            except (json.decoder.JSONDecodeError, yaml.YAMLError, yaml.MarkedYAMLError):
                raise InvalidAPIParameters('Malformed body')
            except t.DataError as e:
                raise InvalidAPIParameters('Input validation error',
                                           extra_data=e.as_dict())
            return await handler(request, checked_params, *args, **kwargs)

        return wrapped

    return wrap


_danger_words = ['password', 'passwd', 'secret']


def mask_sensitive_keys(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Returns a new cloned mapping by masking the values of
    sensitive keys with "***" from the given mapping.
    """
    sanitized = dict()
    for k, v in data.items():
        if any((w in k.lower()) for w in _danger_words):
            sanitized[k] = '***'
        else:
            sanitized[k] = v
    return sanitized


def trim_text(value: str, maxlen: int) -> str:
    if len(value) <= maxlen:
        return value
    value = value[:maxlen - 3] + '...'
    return value


class _Infinity(numbers.Number):

    def __lt__(self, o):
        return False

    def __le__(self, o):
        return False

    def __gt__(self, o):
        return True

    def __ge__(self, o):
        return False

    def __float__(self):
        return float('inf')

    def __int__(self):
        return 0xffff_ffff_ffff_ffff  # a practical 64-bit maximum

    def __hash__(self):
        return hash(self)


numbers.Number.register(_Infinity)
Infinity = _Infinity()


def prettify_traceback(exc):
    # Make a compact stack trace string
    with io.StringIO() as buf:
        while exc is not None:
            print(f'Exception: {exc!r}', file=buf)
            if exc.__traceback__ is None:
                print('  (no traceback available)', file=buf)
            else:
                for frame in traceback.extract_tb(exc.__traceback__):
                    short_path = _rx_sitepkg_path.sub('<sitepkg>/', frame.filename)
                    print(f'  {short_path}:{frame.lineno} ({frame.name})', file=buf)
            exc = exc.__context__
        return f'Traceback:\n{buf.getvalue()}'


def catch_unexpected(log, reraise_cancellation: bool = True, raven=None):
    def _wrap(func):

        @functools.wraps(func)
        async def _wrapped(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except asyncio.CancelledError:
                if reraise_cancellation:
                    raise
            except Exception:
                if raven:
                    raven.captureException()
                log.exception('unexpected error!')
                raise

        return _wrapped

    return _wrap


def set_handler_attr(func, key, value):
    attrs = getattr(func, '_backend_attrs', None)
    if attrs is None:
        attrs = {}
    attrs[key] = value
    setattr(func, '_backend_attrs', attrs)


def get_handler_attr(request, key, default=None):
    # When used in the aiohttp server-side codes, we should use
    # request.match_info.hanlder instead of handler passed to the middleware
    # functions because aiohttp wraps this original handler with functools.partial
    # multiple times to implement its internal middleware processing.
    attrs = getattr(request.match_info.handler, '_backend_attrs', None)
    if attrs is not None:
        return attrs.get(key, default)
    return default


async def not_impl_stub(request) -> web.Response:
    raise QueryNotImplemented


def chunked(iterable, n):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


_burst_last_call: float = 0.0
_burst_times: MutableMapping[Hashable, float] = dict()
_burst_counts: MutableMapping[Hashable, int] = defaultdict(int)


async def call_non_bursty(key: Hashable, coro: Callable[[], Any], *,
                          max_bursts: int = 64,
                          max_idle: Union[int, float] = 100.0):
    '''
    Execute a coroutine once upon max_bursts bursty invocations or max_idle
    milliseconds after bursts smaller than max_bursts.
    '''
    global _burst_last_call, _burst_calls, _burst_counts
    if inspect.iscoroutine(coro):
        # Coroutine objects may not be called before garbage-collected
        # as this function throttles the frequency of invocation.
        # That will generate a bogus warning by the asyncio's debug facility.
        raise TypeError('You must pass coroutine function, not coroutine object.')
    now = time.monotonic()

    if now - _burst_last_call > 3.0:
        # garbage-collect keys
        cleaned_keys = []
        for k, tick in _burst_times.items():
            if now - tick > (max_idle / 1e3):
                cleaned_keys.append(k)
        for k in cleaned_keys:
            del _burst_times[k]
            _burst_counts.pop(k, None)

    last_called = _burst_times.get(key, 0)
    _burst_times[key] = now
    _burst_last_call = now
    invoke = False

    if now - last_called > (max_idle / 1e3):
        invoke = True
        _burst_counts.pop(key, None)
    else:
        _burst_counts[key] += 1
    if _burst_counts[key] >= max_bursts:
        invoke = True
        del _burst_counts[key]

    if invoke:
        if inspect.iscoroutinefunction(coro):
            return await coro()
        else:
            return coro()


class Singleton(type):
    _instances: MutableMapping[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Undefined(metaclass=Singleton):
    pass


undefined = Undefined()
