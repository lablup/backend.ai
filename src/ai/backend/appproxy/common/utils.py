import base64
import enum
import functools
import hashlib
import hmac
import inspect
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Hashable,
    Mapping,
    TypeAlias,
    TypeVar,
)
from uuid import UUID

import humps
import redis
import yaml
from aiohttp import web, web_response
from aiohttp.typedefs import Handler
from aiohttp.web_log import AccessLogger
from pydantic import BaseModel, ValidationError

from ai.backend.appproxy.common.types import PydanticResponse
from ai.backend.common import redis_helper
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.logging import BraceStyleAdapter

from .config import HostPortPair, PermitHashConfig
from .exceptions import InvalidAPIParameters

# FIXME: merge majority of common definitions to ai.backend.common when ready

log = BraceStyleAdapter(logging.getLogger(__spec__.name))
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


def calculate_permit_hash(config: PermitHashConfig, user_id: UUID) -> str:
    hash = hmac.new(
        config.secret, str(user_id).encode("utf-8"), getattr(hashlib, config.digest_mod)
    )
    return base64.b64encode(hash.hexdigest().encode()).decode()


def is_permit_valid(config: PermitHashConfig, user_id: UUID, hash: str) -> bool:
    valid_hash = calculate_permit_hash(config, user_id)
    return valid_hash == hash


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
                case list():
                    json_body = [item.model_dump(mode="json") for item in response.response]
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


def ensure_json_serializable(o: Any) -> Any:
    match o:
        case dict():
            return {ensure_json_serializable(k): ensure_json_serializable(v) for k, v in o.items()}
        case list():
            return [ensure_json_serializable(x) for x in o]
        case UUID():
            return str(o)
        case HostPortPair():
            return {"host": o.host, "port": o.port}
        case Path():
            return o.as_posix()
        case BaseModel():
            return ensure_json_serializable(o.model_dump())
        case enum.Enum():
            return o.value
        case datetime():
            return o.timestamp()
        case _:
            return o


def config_key_to_kebab_case(o: Any) -> Any:
    match o:
        case dict():
            return {humps.kebabize(k): config_key_to_kebab_case(v) for k, v in o.items()}
        case list():
            return [config_key_to_kebab_case(i) for i in o]
        case _:
            return o


def mime_match(base_array: str, compare: str, strict=False) -> bool:
    """
    Checks if `base_array` MIME string contains `compare` MIME type.

    :param: base_array: Array of MIME strings to be compared, concatenated with comma (,) delimiter.
    :param: compare: MIME string to compare.
    :param: strict: If set to True, do not allow wildcard on source MIME type.
    """
    for base in base_array.split(","):
        _base, _, _ = base.partition(";")
        base_left, _, base_right = _base.partition("/")
        compare_left, compare_right = compare.split(";")[0].split("/")
        if (
            not strict
            and (
                (base_left == "*" and base_right == "*")
                or (base_left == compare_left and base_right == "*")
            )
        ) or (base_left == compare_left and base_right == compare_right):
            return True
    return False


class BackendAIAccessLogger(AccessLogger):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def log(self, request, response, time):
        if request.get("do_not_print_access_log"):
            return

        if "request_id" not in request:
            self.logger.warn("Request ID not set at request object!")
            prepend_to_log = ""
        else:
            prepend_to_log = f"#{request['request_id']} "
        if not self.logger.isEnabledFor(logging.INFO):
            # Avoid formatting the log line if it will not be emitted.
            return
        try:
            fmt_info = self._format_line(request, response, time)

            values = list()
            extra = dict()
            for key, value in fmt_info:
                values.append(value)

                if key.__class__ is str:
                    extra[key] = value
                else:
                    k1, k2 = key  # type: ignore[misc]
                    dct = extra.get(k1, {})  # type: ignore[var-annotated,has-type]
                    dct[k2] = value  # type: ignore[index,has-type]
                    extra[k1] = dct  # type: ignore[has-type,assignment]

            self.logger.info((prepend_to_log + self._log_format) % tuple(values), extra=extra)
        except Exception:
            self.logger.exception("Error in logging")


async def ping_redis_connection(connection: RedisConnectionInfo) -> bool:
    try:
        return await redis_helper.execute(connection, lambda r: r.ping())
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        log.exception(f"ping_redis_connection(): Connecting to redis failed: {e}")
        raise e
