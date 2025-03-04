import functools
import inspect
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from inspect import Signature
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Generic,
    Optional,
    Self,
    Type,
    TypeAlias,
    TypeVar,
    get_args,
    get_origin,
)

from aiohttp import web
from aiohttp.web_urldispatcher import UrlMappingMatchInfo
from multidict import CIMultiDictProxy, MultiMapping
from pydantic import BaseModel, ConfigDict
from pydantic_core._pydantic_core import ValidationError

from .exception import (
    InvalidAPIHandlerDefinition,
    InvalidAPIParameters,
    MalformedRequestBody,
    MiddlewareParamParsingFailed,
    ParameterNotParsedError,
)

TModel = TypeVar("TModel", bound=BaseModel)


def convert_validation_error[T](func: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapped(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            raise InvalidAPIParameters(repr(e))

    return wrapped


class BodyParam(Generic[TModel]):
    _model: Type[TModel]
    _parsed: Optional[TModel]

    def __init__(self, model: Type[TModel]) -> None:
        self._model = model
        self._parsed: Optional[TModel] = None

    @property
    def parsed(self) -> TModel:
        if not self._parsed:
            raise ParameterNotParsedError(
                f"Parameter of type {self._model.__name__} has not been parsed yet"
            )
        return self._parsed

    @convert_validation_error
    def from_body(self, json_body: str) -> Self:
        self._parsed = self._model.model_validate(json_body)
        return self


class QueryParam(Generic[TModel]):
    _model: Type[TModel]
    _parsed: Optional[TModel]

    def __init__(self, model: Type[TModel]) -> None:
        self._model = model
        self._parsed: Optional[TModel] = None

    @property
    def parsed(self) -> TModel:
        if not self._parsed:
            raise ParameterNotParsedError(
                f"Parameter of type {self._model.__name__} has not been parsed yet"
            )
        return self._parsed

    @convert_validation_error
    def from_query(self, query: MultiMapping[str]) -> Self:
        self._parsed = self._model.model_validate(query)
        return self


class HeaderParam(Generic[TModel]):
    _model: Type[TModel]
    _parsed: Optional[TModel]

    def __init__(self, model: Type[TModel]) -> None:
        self._model = model
        self._parsed: Optional[TModel] = None

    @property
    def parsed(self) -> TModel:
        if not self._parsed:
            raise ParameterNotParsedError(
                f"Parameter of type {self._model.__name__} has not been parsed yet"
            )
        return self._parsed

    @convert_validation_error
    def from_header(self, headers: CIMultiDictProxy[str]) -> Self:
        self._parsed = self._model.model_validate(headers)
        return self


class PathParam(Generic[TModel]):
    _model: Type[TModel]
    _parsed: Optional[TModel]

    def __init__(self, model: Type[TModel]) -> None:
        self._model = model
        self._parsed: Optional[TModel] = None

    @property
    def parsed(self) -> TModel:
        if not self._parsed:
            raise ParameterNotParsedError(
                f"Parameter of type {self._model.__name__} has not been parsed yet"
            )
        return self._parsed

    @convert_validation_error
    def from_path(self, match_info: UrlMappingMatchInfo) -> Self:
        self._parsed = self._model.model_validate(match_info)
        return self


class MiddlewareParam(ABC, BaseModel):
    @classmethod
    @abstractmethod
    def from_request(cls, request: web.Request) -> Self:
        pass


class BaseRequestModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class BaseResponseModel(BaseModel):
    pass


JSONDict: TypeAlias = dict[str, Any]


@dataclass
class APIResponse:
    _status_code: int
    _data: Optional[BaseResponseModel]

    @classmethod
    def build(cls, status_code: int, response_model: BaseResponseModel) -> Self:
        return cls(_status_code=status_code, _data=response_model)

    @classmethod
    def no_content(cls, status_code: int) -> Self:
        return cls(_status_code=status_code, _data=None)

    @property
    def to_json(self) -> Optional[JSONDict]:
        return self._data.model_dump(mode="json") if self._data else None

    @property
    def status_code(self) -> int:
        return self._status_code


_ParamType: TypeAlias = BodyParam | QueryParam | PathParam | HeaderParam | MiddlewareParam
_ParserType: TypeAlias = BodyParam | QueryParam | PathParam | HeaderParam | type[MiddlewareParam]


async def _extract_param_value(request: web.Request, input_param_type: Any) -> _ParamType:
    try:
        # MiddlewareParam Type
        if get_origin(input_param_type) is None and issubclass(input_param_type, MiddlewareParam):
            try:
                return input_param_type.from_request(request)
            except ValidationError:
                raise MiddlewareParamParsingFailed(f"Failed while parsing {input_param_type}")

        # If origin type name is BodyParam/QueryParam/HeaderParam/PathParam
        origin_type = get_origin(input_param_type)
        pydantic_model = get_args(input_param_type)[0]
        param_instance = input_param_type(pydantic_model)

        if origin_type is BodyParam:
            if not request.can_read_body:
                raise MalformedRequestBody(
                    f"Malformed body - URL: {request.url}, Method: {request.method}"
                )
            try:
                body = await request.json()
            except json.decoder.JSONDecodeError:
                raise MalformedRequestBody(
                    f"Malformed body - URL: {request.url}, Method: {request.method}"
                )
            return param_instance.from_body(body)

        elif origin_type is QueryParam:
            return param_instance.from_query(request.query)

        elif origin_type is HeaderParam:
            return param_instance.from_header(request.headers)

        elif origin_type is PathParam:
            return param_instance.from_path(request.match_info)

        else:
            raise InvalidAPIParameters(
                f"Parameter '{input_param_type}' must use one of QueryParam, PathParam, HeaderParam, MiddlewareParam, BodyParam"
            )

    except ValidationError as e:
        raise InvalidAPIParameters(str(e))


class _HandlerParameters:
    _params: dict[str, _ParamType]

    def __init__(self) -> None:
        self._params: dict[str, _ParamType] = {}

    def add(self, name: str, value: _ParamType) -> None:
        if value is not None:
            self._params[name] = value

    def get_all(self) -> dict[str, _ParamType]:
        return self._params


HandlerReturn = Awaitable[APIResponse] | Coroutine[Any, Any, APIResponse]

BaseHandler: TypeAlias = Callable[..., HandlerReturn]
ParsedRequestHandler: TypeAlias = Callable[..., Awaitable[web.StreamResponse]]


async def _parse_and_execute_handler(
    request: web.Request, handler: BaseHandler, signature: Signature
) -> web.StreamResponse:
    handler_params = _HandlerParameters()
    for name, param in signature.parameters.items():
        # If handler has no parameter, for loop is skipped
        # Raise error when parameter exists and has no type hint or not wrapped by 'Annotated'
        if param.annotation is inspect.Parameter.empty:
            raise InvalidAPIParameters(
                f"Type hint or Annotated must be added in API handler signature: {param.name}"
            )

        value = await _extract_param_value(request=request, input_param_type=param.annotation)

        if not value:
            raise InvalidAPIParameters(
                f"Type hint or Annotated must be added in API handler signature: {param.name}"
            )

        handler_params.add(name, value)

    response = await handler(**handler_params.get_all())

    if not isinstance(response, APIResponse):
        raise InvalidAPIParameters(
            f"Only Response wrapped by APIResponse Class can be handle: {type(response)}"
        )

    return web.json_response(
        response.to_json,
        status=response.status_code,
    )


def _register_parameter_parser(
    signature: Signature,
    *,
    handler_name: str,
) -> dict[str, _ParserType]:
    signature_parser_map: dict[str, _ParserType] = {}
    for name, param in signature.parameters.items():
        if param.annotation is inspect.Parameter.empty:
            raise InvalidAPIHandlerDefinition(
                f"Not allowed signature for API handler function (handler:{handler_name},name:{name})"
            )
        param_type = param.annotation
        original_type = get_origin(param_type)
        if original_type is None:
            if issubclass(param_type, MiddlewareParam):
                signature_parser_map[name] = param_type
                continue
            else:
                raise InvalidAPIHandlerDefinition(
                    f"Not allowed signature for API handler function. (handler:{handler_name}, name:{name}, type:{original_type})"
                )
        model_args = get_args(param_type)
        try:
            validation_model = model_args[0]
        except IndexError:
            raise InvalidAPIHandlerDefinition(
                f"API parameter model got no argument (handler:{handler_name}, name:{name}, type:{original_type})"
            )

        param_instance = param_type(validation_model)
        signature_parser_map[name] = param_instance
    return signature_parser_map


async def _serialize_parameter(
    request: web.Request, param_instance_or_class: _ParserType
) -> _ParamType:
    param_instance: _ParamType
    match param_instance_or_class:
        case BodyParam():
            if not request.can_read_body:
                raise MalformedRequestBody(
                    f"Malformed body - URL: {request.url}, Method: {request.method}"
                )
            try:
                body = await request.json()
            except json.decoder.JSONDecodeError as e:
                raise MalformedRequestBody(
                    f"Malformed body - URL: {request.url}, Method: {request.method}, error: {repr(e)}"
                )
            return param_instance_or_class.from_body(body)
        case QueryParam():
            return param_instance_or_class.from_query(request.query)
        case HeaderParam():
            return param_instance_or_class.from_header(request.headers)
        case PathParam():
            return param_instance_or_class.from_path(request.match_info)
        case _:
            try:
                param_instance = param_instance_or_class.from_request(request)
            except ValidationError as e:
                raise MiddlewareParamParsingFailed(
                    f"Failed while parsing {param_instance_or_class}. (error:{repr(e)})"
                )
    return param_instance


def _parse_response(response: APIResponse) -> web.Response:
    return web.json_response(
        data=response.to_json,
        status=response.status_code,
    )


def api_handler(handler: BaseHandler) -> ParsedRequestHandler:
    """
    This decorator processes HTTP request parameters using Pydantic models.
    NOTICE: API hander methods must be classmethod. It handlers are not class methods it will not work as intended

    1. Request Body:
        @api_handler
        async def handler(body: BodyParam[UserModel]):  # UserModel is a Pydantic model
            user = body.parsed                          # 'parsed' property gets pydantic model you defined
            # Response model should inherit BaseResponseModel
            return APIResponse.build(status_code=200, response_model=YourResponseModel(user=user.id))

    2. Query Parameters:
        @api_handler
        async def handler(query: QueryParam[QueryPathModel]):
            parsed_query = query.parsed
            return APIResponse.build(status_code=200, response_model=YourResponseModel(search=parsed_query.query))

    3. Headers:
        @api_handler
        async def handler(headers: HeaderParam[HeaderModel]):
            parsed_header = headers.parsed
            return APIResponse.build(status_code=200, response_model=YourResponseModel(data=parsed_header.token))

    4. Path Parameters:
        @api_handler
        async def handler(path: PathParam[PathModel]):
            parsed_path = path.parsed
            return APIResponse.build(status_code=200, response_model=YourResponseModel(path=parsed_path))

    5. Middleware Parameters:
        # Need to extend MiddlewareParam and implement 'from_request'
        class AuthMiddlewareParam(MiddlewareParam):
            user_id: str
            user_email: str
            @classmethod
            def from_request(cls, request: web.Request) -> Self:
                # Extract and validate data from request
                user_id = request["user"]["uuid"]
                user_email = request["user"]["email"]
                return cls(user_id=user_id)

        @api_handler
        async def handler(auth: AuthMiddlewareParam):   # No generic, so no need to call 'parsed'
            return APIResponse(status_code=200, response_model=YourResponseModel(author_name=auth.name))

    6. Multiple Parameters:
        @api_handler
        async def handler(
            user: BodyParam[UserModel],  # body
            query: QueryParam[QueryModel],  # query parameters
            headers: HeaderParam[HeaderModel],  # headers
            auth: AuthMiddleware,  # middleware parameter
        ):
            return APIResponse(
                status_code=200,
                response_model=YourResponseModel(
                    user=user.parsed.user_id,
                    query=query.parsed.page,
                    headers=headers.parsed.auth,
                    user_id=auth.user_id
                )
            )

    Note:
    - All parameters must have type hints or wrapped by Annotated
    - Response class must be APIResponse and your response model should inherit BaseResponseModel
    - Request body is parsed must be json format
    - MiddlewareParam classes must implement the from_request classmethod
    """

    original_signature: Signature = inspect.signature(handler)

    sanitized_signature = original_signature.replace(
        parameters=list(original_signature.parameters.values())[1:]
    )
    signature_parser_map = _register_parameter_parser(
        sanitized_signature, handler_name=str(handler)
    )

    @functools.wraps(handler)
    async def wrapped(first_arg: Any, request: web.Request) -> web.Response:
        kwargs: dict[str, _ParamType] = {}
        for name, param_instance_or_class in signature_parser_map.items():
            param_instance = await _serialize_parameter(request, param_instance_or_class)
            kwargs[name] = param_instance
        response = await handler(first_arg, **kwargs)
        return _parse_response(response)

    return wrapped
