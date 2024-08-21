import asyncio
import functools
import inspect
import io
import itertools
import json
import logging
import numbers
import re
import time
import traceback
import uuid
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Hashable,
    Mapping,
    MutableMapping,
    Optional,
    ParamSpec,
    Tuple,
    TypeAlias,
    TypeVar,
    Union,
)

import sqlalchemy as sa
import trafaret as t
import yaml
from aiohttp import web
from aiohttp.typedefs import Handler
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AccessKey

from ..models import UserRole, users
from ..utils import (
    check_if_requester_is_eligible_to_act_as_target_access_key,
    check_if_requester_is_eligible_to_act_as_target_user_uuid,
)
from .exceptions import (
    DeprecatedAPI,
    GenericForbidden,
    InvalidAPIParameters,
    NotImplementedAPI,
)

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_rx_sitepkg_path = re.compile(r"^.+/site-packages/")


def method_placeholder(orig_method):
    async def _handler(request):
        raise web.HTTPMethodNotAllowed(request.method, [orig_method])

    return _handler


async def get_access_key_scopes(
    request: web.Request, params: Any = None
) -> Tuple[AccessKey, AccessKey]:
    if not request["is_authorized"]:
        raise GenericForbidden("Only authorized requests may have access key scopes.")
    root_ctx: RootContext = request.app["_root.context"]
    owner_access_key: Optional[AccessKey] = (params or {}).get("owner_access_key", None)
    if owner_access_key is None or owner_access_key == request["keypair"]["access_key"]:
        return request["keypair"]["access_key"], request["keypair"]["access_key"]
    async with root_ctx.db.begin_readonly() as conn:
        try:
            await check_if_requester_is_eligible_to_act_as_target_access_key(
                conn,
                request["user"]["role"],
                request["user"]["domain_name"],
                owner_access_key,
            )
            return request["keypair"]["access_key"], owner_access_key
        except ValueError as e:
            raise InvalidAPIParameters(str(e))
        except RuntimeError as e:
            raise GenericForbidden(str(e))


async def get_user_uuid_scopes(
    request: web.Request, params: Any = None
) -> Tuple[uuid.UUID, uuid.UUID]:
    if not request["is_authorized"]:
        raise GenericForbidden("Only authorized requests may have access key scopes.")
    root_ctx: RootContext = request.app["_root.context"]
    owner_uuid: Optional[uuid.UUID] = (params or {}).get("owner_uuid", None)
    if owner_uuid is None or owner_uuid == request["user"]["uuid"]:
        return request["user"]["uuid"], request["user"]["uuid"]
    async with root_ctx.db.begin_readonly() as conn:
        try:
            await check_if_requester_is_eligible_to_act_as_target_user_uuid(
                conn,
                request["user"]["role"],
                request["user"]["domain_name"],
                owner_uuid,
            )
            return request["user"]["uuid"], owner_uuid
        except ValueError as e:
            raise InvalidAPIParameters(str(e))
        except RuntimeError as e:
            raise GenericForbidden(str(e))


async def get_user_scopes(
    request: web.Request,
    params: Optional[dict[str, Any]] = None,
) -> tuple[uuid.UUID, UserRole]:
    root_ctx: RootContext = request.app["_root.context"]
    if not request["is_authorized"]:
        raise GenericForbidden("Only authorized requests may have user scopes.")
    if params is not None and (owner_user_email := params.get("owner_user_email")) is not None:
        if not request["is_superadmin"]:
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
            owner_user_uuid = row["uuid"]
            owner_user_role = row["role"]
            owner_user_domain = row["domain_name"]
        if request["is_superadmin"]:
            pass
        elif request["is_admin"]:
            if request["user"]["domain_name"] != owner_user_domain:
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
        owner_user_uuid = request["user"]["uuid"]
        owner_user_role = request["user"]["role"]
    return owner_user_uuid, owner_user_role


P = ParamSpec("P")
TParamTrafaret = TypeVar("TParamTrafaret", bound=t.Trafaret)
TQueryTrafaret = TypeVar("TQueryTrafaret", bound=t.Trafaret)
TAnyResponse = TypeVar("TAnyResponse", bound=web.StreamResponse)


def check_api_params(
    checker: TParamTrafaret,
    loads: Callable[[str], Any] | None = None,
    query_param_checker: TQueryTrafaret | None = None,
    request_examples: list[Any] | None = None,
) -> Callable[
    # We mark the arg for the validated param as Any because we cannot define a generic type of
    # Trafaret's return value.
    [Callable[Concatenate[web.Request, Any, P], Awaitable[TAnyResponse]]],
    Callable[Concatenate[web.Request, P], Awaitable[TAnyResponse]],
]:
    def wrap(handler: Callable[Concatenate[web.Request, Any, P], Awaitable[TAnyResponse]]):
        @functools.wraps(handler)
        async def wrapped(request: web.Request, *args: P.args, **kwargs: P.kwargs) -> TAnyResponse:
            orig_params: Any
            body: str = ""
            try:
                body_exists = request.can_read_body
                if body_exists and request.method not in ("GET", "HEAD"):
                    body = await request.text()
                    if request.content_type == "text/yaml":
                        orig_params = yaml.load(body, Loader=yaml.BaseLoader)
                    else:
                        orig_params = (loads or json.loads)(body)
                else:
                    orig_params = dict(request.query)
                stripped_params = orig_params.copy()
                log.debug("stripped raw params: {}", mask_sensitive_keys(stripped_params))
                checked_params = checker.check(stripped_params)
                if body_exists and query_param_checker:
                    query_params = query_param_checker.check(request.query)
                    kwargs["query"] = query_params
            except (json.decoder.JSONDecodeError, yaml.YAMLError, yaml.MarkedYAMLError):
                raise InvalidAPIParameters("Malformed body")
            except t.DataError as e:
                raise InvalidAPIParameters("Input validation error", extra_data=e.as_dict())
            return await handler(request, checked_params, *args, **kwargs)

        set_handler_attr(wrapped, "request_scheme", checker)
        if request_examples:
            set_handler_attr(wrapped, "request_examples", request_examples)
        return wrapped

    return wrap


class BaseResponseModel(BaseModel):
    status: Annotated[int, Field(strict=True, exclude=True, ge=100, lt=600)] = 200


TParamModel = TypeVar("TParamModel", bound=BaseModel)
TQueryModel = TypeVar("TQueryModel", bound=BaseModel)
TResponseModel = TypeVar("TResponseModel", bound=BaseModel)

TPydanticResponse: TypeAlias = TResponseModel | list
THandlerFuncWithoutParam: TypeAlias = Callable[
    Concatenate[web.Request, P], Awaitable[TPydanticResponse | TAnyResponse]
]
THandlerFuncWithParam: TypeAlias = Callable[
    Concatenate[web.Request, TParamModel, P], Awaitable[TPydanticResponse | TAnyResponse]
]


def ensure_stream_response_type(
    response: BaseResponseModel | BaseModel | list[TResponseModel] | web.StreamResponse,
) -> web.StreamResponse:
    match response:
        case BaseResponseModel(status=status):
            return web.json_response(response.model_dump(mode="json"), status=status)
        case BaseModel():
            return web.json_response(response.model_dump(mode="json"))
        case list():
            return web.json_response(TypeAdapter(type(response)).dump_python(response, mode="json"))
        case web.StreamResponse():
            return response
        case _:
            raise RuntimeError(f"Unsupported response type ({type(response)})")


def pydantic_response_api_handler(
    handler: THandlerFuncWithoutParam,
) -> Handler:
    """
    Only for API handlers which does not require request body.
    For handlers with params to consume use @pydantic_params_api_handler() or
    @check_api_params() decorator (only when request param is validated with trafaret).
    """

    @functools.wraps(handler)
    async def wrapped(
        request: web.Request, *args: P.args, **kwargs: P.kwargs
    ) -> web.StreamResponse:
        response = await handler(request, *args, **kwargs)
        return ensure_stream_response_type(response)

    return wrapped


def pydantic_params_api_handler(
    checker: type[TParamModel],
    loads: Callable[[str], Any] | None = None,
    query_param_checker: type[TQueryModel] | None = None,
) -> Callable[[THandlerFuncWithParam], Handler]:
    def wrap(
        handler: THandlerFuncWithParam,
    ) -> Handler:
        @functools.wraps(handler)
        async def wrapped(
            request: web.Request, *args: P.args, **kwargs: P.kwargs
        ) -> web.StreamResponse:
            orig_params: Any
            body: str = ""
            try:
                body_exists = request.can_read_body
                if body_exists:
                    body = await request.text()
                    if request.content_type == "text/yaml":
                        orig_params = yaml.load(body, Loader=yaml.BaseLoader)
                    else:
                        orig_params = (loads or json.loads)(body)
                else:
                    orig_params = dict(request.query)
                stripped_params = orig_params.copy()
                log.debug("stripped raw params: {}", mask_sensitive_keys(stripped_params))
                checked_params = checker.model_validate(stripped_params)
                if body_exists and query_param_checker:
                    query_params = query_param_checker.model_validate(request.query)
                    kwargs["query"] = query_params
            except (json.decoder.JSONDecodeError, yaml.YAMLError, yaml.MarkedYAMLError):
                raise InvalidAPIParameters("Malformed body")
            except ValidationError as e:
                raise InvalidAPIParameters("Input validation error", extra_data=e.errors())
            result = await handler(request, checked_params, *args, **kwargs)
            return ensure_stream_response_type(result)

        set_handler_attr(wrapped, "request_scheme", checker)

        return wrapped

    return wrap


_danger_words = ["password", "passwd", "secret"]


def mask_sensitive_keys(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Returns a new cloned mapping by masking the values of
    sensitive keys with "***" from the given mapping.
    """
    sanitized = dict()
    for k, v in data.items():
        if any((w in k.lower()) for w in _danger_words):
            sanitized[k] = "***"
        else:
            sanitized[k] = v
    return sanitized


def trim_text(value: str, maxlen: int) -> str:
    if len(value) <= maxlen:
        return value
    value = value[: maxlen - 3] + "..."
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
        return float("inf")

    def __int__(self):
        return 0xFFFF_FFFF_FFFF_FFFF  # a practical 64-bit maximum

    def __hash__(self):
        return hash(self)


numbers.Number.register(_Infinity)
Infinity = _Infinity()


def prettify_traceback(exc):
    # Make a compact stack trace string
    with io.StringIO() as buf:
        while exc is not None:
            print(f"Exception: {exc!r}", file=buf)
            if exc.__traceback__ is None:
                print("  (no traceback available)", file=buf)
            else:
                for frame in traceback.extract_tb(exc.__traceback__):
                    short_path = _rx_sitepkg_path.sub("<sitepkg>/", frame.filename)
                    print(f"  {short_path}:{frame.lineno} ({frame.name})", file=buf)
            exc = exc.__context__
        return f"Traceback:\n{buf.getvalue()}"


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
                log.exception("unexpected error!")
                raise

        return _wrapped

    return _wrap


def set_handler_attr(func, key, value):
    attrs = getattr(func, "_backend_attrs", None)
    if attrs is None:
        attrs = {}
    attrs[key] = value
    setattr(func, "_backend_attrs", attrs)


def get_handler_attr(request, key, default=None):
    # When used in the aiohttp server-side codes, we should use
    # request.match_info.hanlder instead of handler passed to the middleware
    # functions because aiohttp wraps this original handler with functools.partial
    # multiple times to implement its internal middleware processing.
    attrs = getattr(request.match_info.handler, "_backend_attrs", None)
    if attrs is not None:
        return attrs.get(key, default)
    return default


async def not_impl_stub(request: web.Request) -> web.Response:
    raise NotImplementedAPI


def deprecated_stub(msg: str) -> Callable[[web.Request], Awaitable[web.StreamResponse]]:
    async def deprecated_stub_impl(request: web.Request) -> web.Response:
        raise DeprecatedAPI(extra_msg=msg)

    return deprecated_stub_impl


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


async def call_non_bursty(
    key: Hashable,
    coro: Callable[[], Any],
    *,
    max_bursts: int = 64,
    max_idle: Union[int, float] = 100.0,
):
    """
    Execute a coroutine once upon max_bursts bursty invocations or max_idle
    milliseconds after bursts smaller than max_bursts.
    """
    global _burst_last_call, _burst_times, _burst_counts
    if inspect.iscoroutine(coro):
        # Coroutine objects may not be called before garbage-collected
        # as this function throttles the frequency of invocation.
        # That will generate a bogus warning by the asyncio's debug facility.
        raise TypeError("You must pass coroutine function, not coroutine object.")
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
