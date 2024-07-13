import functools
import inspect
import json
import time
from collections import defaultdict
from typing import (
    Any,
    Awaitable,
    Callable,
    Hashable,
    Literal,
    Mapping,
    TypeAlias,
    TypeVar,
)

import yaml
from aiohttp import web, web_response
from aiohttp.typedefs import Handler
from pydantic import BaseModel, ValidationError

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.wsproxy.defs import RootContext
from ai.backend.wsproxy.exceptions import AuthorizationFailed

from ..exceptions import InvalidAPIParameters
from ..types import PydanticResponse


def auth_required(scope: Literal["manager"] | Literal["worker"]) -> Callable[[Handler], Handler]:
    def wrap(handler: Handler) -> Handler:
        @functools.wraps(handler)
        async def wrapped(request: web.Request, *args, **kwargs):
            root_ctx: RootContext = request.app["_root.context"]
            permitted_token = root_ctx.local_config.wsproxy.api_secret
            permitted_header_values = (
                permitted_token,
                f"Bearer {permitted_token}",
                f"BackendAI {permitted_token}",
            )
            token_to_evaluate = request.headers.get("X-BackendAI-Token")
            if token_to_evaluate not in permitted_header_values:
                raise AuthorizationFailed("Unauthorized access")
            return await handler(request, *args, **kwargs)

        original_attrs = getattr(handler, "_backend_attrs", {})
        for k, v in original_attrs.items():
            set_handler_attr(wrapped, k, v)

        set_handler_attr(wrapped, "auth_scope", scope)
        return wrapped

    return wrap


# FIXME: merge majority of common definitions to ai.backend.common when ready

_danger_words = ["password", "passwd", "secret"]


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


_burst_last_call: float = 0.0
_burst_times: dict[Hashable, float] = dict()
_burst_counts: dict[Hashable, int] = defaultdict(int)


async def call_non_bursty(
    key: Hashable,
    coro: Callable[[], Any],
    *,
    max_bursts: int = 64,
    max_idle: int | float = 100.0,
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


TAnyResponse = TypeVar("TAnyResponse", bound=web.StreamResponse)

TParamModel = TypeVar("TParamModel", bound=BaseModel)
TQueryModel = TypeVar("TQueryModel", bound=BaseModel)
TResponseModel = TypeVar("TResponseModel", bound=BaseModel)

THandlerFuncWithoutParam: TypeAlias = Callable[
    [web.Request], Awaitable[PydanticResponse | TAnyResponse]
]
THandlerFuncWithParam: TypeAlias = Callable[
    [web.Request, TParamModel], Awaitable[PydanticResponse | TAnyResponse]
]


def ensure_stream_response_type(
    response: PydanticResponse | TAnyResponse,
) -> web.StreamResponse:
    json_body: Any
    match response:
        case PydanticResponse():
            match response.response:
                case BaseModel():
                    json_body = response.response.model_dump(mode="json")
                case _:
                    raise RuntimeError(f"Unsupported model type ({type(response.response)})")
            return web.json_response(json_body, headers=response.headers, status=response.status)
        case web_response.StreamResponse():
            return response
        case _:
            raise RuntimeError(f"Unsupported response type ({type(response)})")


def pydantic_api_response_handler(
    handler: THandlerFuncWithoutParam,
    is_deprecated=False,
) -> Handler:
    """
    Only for API handlers which does not require request body.
    For handlers with params to consume use @pydantic_params_api_handler() or
    @check_api_params() decorator (only when request param is validated with trafaret).
    """

    @functools.wraps(handler)
    async def wrapped(
        request: web.Request,
        *args,
        **kwargs,
    ) -> web.StreamResponse:
        response = await handler(request, *args, **kwargs)
        return ensure_stream_response_type(response)

    set_handler_attr(wrapped, "deprecated", is_deprecated)
    return wrapped


def pydantic_api_handler(
    checker: type[TParamModel],
    loads: Callable[[str], Any] | None = None,
    query_param_checker: type[TQueryModel] | None = None,
    is_deprecated=False,
) -> Callable[[THandlerFuncWithParam], Handler]:
    def wrap(
        handler: THandlerFuncWithParam,
    ) -> Handler:
        @functools.wraps(handler)
        async def wrapped(
            request: web.Request,
            *args,
            **kwargs,
        ) -> web.StreamResponse:
            orig_params: Any
            body: str = ""
            log: BraceStyleAdapter = request["log"]
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

        original_attrs = getattr(handler, "_backend_attrs", {})
        for k, v in original_attrs.items():
            set_handler_attr(wrapped, k, v)

        set_handler_attr(wrapped, "request_scheme", checker)
        set_handler_attr(wrapped, "deprecated", is_deprecated)

        return wrapped

    return wrap
