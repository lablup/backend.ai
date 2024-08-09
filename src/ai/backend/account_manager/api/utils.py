import functools
import json
from dataclasses import dataclass, field
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Mapping,
    TypeAlias,
    TypeVar,
)

import yaml
from aiohttp import web, web_response
from aiohttp.typedefs import Handler
from pydantic import BaseModel, ConfigDict, ValidationError

from ai.backend.common.logging import BraceStyleAdapter

from ..defs import AUTH_REQUIRED_ATTR_KEY, CLIENT_ROLE_ATTR_KEY
from ..exceptions import AuthorizationFailed, InvalidAPIParameters
from ..types import UserRole


def auth_required(role: UserRole) -> Callable[[Handler], Handler]:
    def wrapper(handler: Handler) -> Handler:
        @functools.wraps(handler)
        async def wrapped(request: web.Request, *args, **kwargs):
            client_role: UserRole | None = request.get(CLIENT_ROLE_ATTR_KEY)
            match role:
                case UserRole.ADMIN:
                    if client_role != role:
                        raise AuthorizationFailed("Unauthorized access")
                case UserRole.USER:
                    if client_role not in (UserRole.ADMIN, UserRole.USER):
                        raise AuthorizationFailed("Unauthorized access")
            return await handler(request, *args, **kwargs)

        set_handler_attr(wrapped, AUTH_REQUIRED_ATTR_KEY, True)
        return wrapped

    return wrapper


def set_handler_attr(func, key, value):
    attrs = getattr(func, "_backend_attrs", None)
    if attrs is None:
        attrs = {}
    attrs[key] = value
    setattr(func, "_backend_attrs", attrs)


def get_handler_attr(request: web.Request, key: str, default: Any = None):
    # When used in the aiohttp server-side codes, we should use
    # request.match_info.hanlder instead of handler passed to the middleware
    # functions because aiohttp wraps this original handler with functools.partial
    # multiple times to implement its internal middleware processing.
    attrs = getattr(request.match_info.handler, "_backend_attrs", None)
    if attrs is not None:
        return attrs.get(key, default)
    return default


# FIXME: merge majority of common definitions to ai.backend.common when ready

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


TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


class RequestData(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )


@dataclass
class ResponseModel(Generic[TBaseModel]):
    data: TBaseModel
    headers: dict[str, Any] = field(default_factory=dict)
    status: int = 200


TAnyResponse = TypeVar("TAnyResponse", bound=web.StreamResponse)

TParamModel = TypeVar("TParamModel", bound=BaseModel)
TQueryModel = TypeVar("TQueryModel", bound=BaseModel)
TResponseModel = TypeVar("TResponseModel", bound=BaseModel)

THandlerFuncWithoutParam: TypeAlias = Callable[
    [web.Request], Awaitable[ResponseModel | TAnyResponse]
]
THandlerFuncWithParam: TypeAlias = Callable[
    [web.Request, TParamModel], Awaitable[ResponseModel | TAnyResponse]
]


def ensure_stream_response_type(
    response: ResponseModel | TAnyResponse,
) -> web.StreamResponse:
    json_body: Any
    match response:
        case ResponseModel():
            match response.data:
                case BaseModel():
                    json_body = response.data.model_dump(mode="json")
                case _:
                    raise RuntimeError(f"Unsupported model type ({type(response.data)})")
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
