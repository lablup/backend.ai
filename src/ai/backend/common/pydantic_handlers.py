import functools
import inspect
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Optional, Self, Type, TypeVar, get_args, get_origin

from aiohttp import web
from aiohttp.web_urldispatcher import UrlMappingMatchInfo
from multidict import CIMultiDictProxy, MultiMapping
from pydantic import BaseModel
from pydantic_core._pydantic_core import ValidationError

from .exception import (
    InvalidAPIParameters,
    MalformedRequestBody,
    MiddlewareParamParsingFailed,
    ParameterNotParsedError,
)

T = TypeVar("T", bound=BaseModel)


class BodyParam(Generic[T]):
    _model: Type[T]
    _parsed: Optional[T]

    def __init__(self, model: Type[T]) -> None:
        self._model = model
        self._parsed: Optional[T] = None

    @property
    def parsed(self) -> T:
        if not self._parsed:
            raise ParameterNotParsedError()
        return self._parsed

    def from_body(self, json_body: str) -> Self:
        self._parsed = self._model.model_validate(json_body)
        return self


class QueryParam(Generic[T]):
    _model: Type[T]
    _parsed: Optional[T]

    def __init__(self, model: Type[T]) -> None:
        self._model = model
        self._parsed: Optional[T] = None

    @property
    def parsed(self) -> T:
        if not self._parsed:
            raise ParameterNotParsedError()
        return self._parsed

    def from_query(self, query: MultiMapping[str]) -> Self:
        self._parsed = self._model.model_validate(query)
        return self


class HeaderParam(Generic[T]):
    _model: Type[T]
    _parsed: Optional[T]

    def __init__(self, model: Type[T]) -> None:
        self._model = model
        self._parsed: Optional[T] = None

    @property
    def parsed(self) -> T:
        if not self._parsed:
            raise ParameterNotParsedError()
        return self._parsed

    def from_header(self, headers: CIMultiDictProxy[str]) -> Self:
        self._parsed = self._model.model_validate(headers)
        return self


class PathParam(Generic[T]):
    _model: Type[T]
    _parsed: Optional[T]

    def __init__(self, model: Type[T]) -> None:
        self._model = model
        self._parsed: Optional[T] = None

    @property
    def parsed(self) -> T:
        if not self._parsed:
            raise ParameterNotParsedError()
        return self._parsed

    def from_path(self, match_info: UrlMappingMatchInfo) -> Self:
        self._parsed = self._model.model_validate(match_info)
        return self


class MiddlewareParam(ABC, BaseModel):
    @classmethod
    @abstractmethod
    def from_request(cls, request: web.Request) -> Self:
        pass


@dataclass
class BaseResponse:
    data: BaseModel
    status_code: int


_ParamType = BodyParam | QueryParam | PathParam | HeaderParam | MiddlewareParam


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


async def _pydantic_handler(request: web.Request, handler) -> web.Response:
    signature = inspect.signature(handler)
    handler_params = _HandlerParameters()
    for name, param in signature.parameters.items():
        # Raise error when parameter has no type hint or not wrapped by 'Annotated'
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

    if not isinstance(response, BaseResponse):
        raise InvalidAPIParameters(
            f"Only Response wrapped by BaseResponse Class can be handle: {type(response)}"
        )

    return web.json_response(response.data.model_dump(mode="json"), status=response.status_code)


def pydantic_api_handler(handler):
    """
    This decorator processes HTTP request parameters using Pydantic models.

    1. Request Body:
        @pydantic_api_handler
        async def handler(body: BodyParam[UserModel]):  # UserModel is a Pydantic model
            user = body.parsed                          # 'parsed' property gets pydantic model you defined
            return BaseResponse(data=YourResponseModel(user=user.id))

    2. Query Parameters:
        @pydantic_api_handler
        async def handler(query: QueryParam[QueryPathModel]):
            parsed_query = query.parsed
            return BaseResponse(data=YourResponseModel(search=parsed_query.query))

    3. Headers:
        @pydantic_api_handler
        async def handler(headers: HeaderParam[HeaderModel]):
            parsed_header = headers.parsed
            return BaseResponse(data=YourResponseModel(data=parsed_header.token))

    4. Path Parameters:
        @pydantic_api_handler
        async def handler(path: PathModel = PathParam(PathModel)):
            parsed_path = path.parsed
            return BaseResponse(data=YourResponseModel(path=parsed_path))

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

        @pydantic_api_handler
        async def handler(auth: AuthMiddlewareParam):  # No generic, so no need to call 'parsed'
            return BaseResponse(data=YourResponseModel(author_name=auth.name))

    6. Multiple Parameters:
        @pydantic_api_handler
        async def handler(
            user: BodyParam[UserModel],  # body
            query: QueryParam[QueryModel],  # query parameters
            headers: HeaderParam[HeaderModel],  # headers
            auth: AuthMiddleware,  # middleware parameter
        ):
            return BaseResponse(data=YourResponseModel(
                    user=user.parsed.user_id,
                    query=query.parsed.page,
                    headers=headers.parsed.auth,
                    user_id=auth.user_id
                )
            )

    Note:
    - All parameters must have type hints or wrapped by Annotated
    - Response class must be BaseResponse. put your response model in BaseResponse.data
    - Request body is parsed must be json format
    - MiddlewareParam classes must implement the from_request classmethod
    """

    @functools.wraps(handler)
    async def wrapped(request: web.Request, *args, **kwargs) -> web.Response:
        return await _pydantic_handler(request, handler)

    return wrapped
