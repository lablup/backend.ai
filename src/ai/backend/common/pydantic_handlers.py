import functools
import inspect
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Optional, Self, Type, TypeVar

import yaml
from aiohttp import web
from pydantic import BaseModel

from .exception import InvalidAPIParametersModel, MalformedRequestBody

T = TypeVar("T", bound=BaseModel)


class Param(ABC, Generic[T]):
    @abstractmethod
    def from_request(self, request: web.Request) -> T:
        pass


class QueryParam(Param[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def from_request(self, request: web.Request) -> T:
        return self.model.model_validate(request.query)


class HeaderParam(Param[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def from_request(self, request: web.Request) -> T:
        return self.model.model_validate(request.headers)


class PathParam(Param[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def from_request(self, request: web.Request) -> T:
        return self.model.model_validate(request.match_info)


class MiddlewareParam(Param):
    @abstractmethod
    def from_request(cls, request: web.Request) -> Self:
        pass


@dataclass
class Parameter:
    name: str
    model: Type[BaseModel]
    default: Any


async def extract_param_value(request: web.Request, param: Parameter) -> Optional[Any]:
    match param:
        # MiddlewareParam Type
        case Parameter(model=model) if isinstance(model, type) and isinstance(
            model, MiddlewareParam
        ):
            return model.from_request(request)

        # HeaderParam, QueryParam, PathParam Type
        case Parameter(default=default) if isinstance(default, Param):
            return default.from_request(request)

        # Body
        case Parameter(model=model) if isinstance(model, type) and not issubclass(model, Param):
            if not request.can_read_body:
                raise MalformedRequestBody(
                    f"Malformed body - URL: {request.url}, Method: {request.method}"
                )

            body = await request.text()
            if not body:
                raise MalformedRequestBody(
                    f"Malformed body - URL: {request.url}, Method: {request.method}"
                )

            if request.content_type == "text/yaml":
                data = yaml.load(body, Loader=yaml.BaseLoader)
            else:
                data = json.loads(body)

            return model.model_validate(data)

        case _:
            raise InvalidAPIParametersModel(
                f"Parameter '{param.name}' must be MiddlewareParam, use Param as default value, or be a BaseModel for body"
            )


class HandlerParameters:
    def __init__(self):
        self.params: dict[str, Any] = {}

    def add(self, name: str, value: Any) -> None:
        if value is not None:
            self.params[name] = value

    def get_all(self) -> dict[str, Any]:
        return self.params


async def pydantic_handler(request: web.Request, handler) -> web.Response:
    signature = inspect.signature(handler)
    handler_params = HandlerParameters()
    for name, param in signature.parameters.items():
        # Raise error when parameter has no type hint or not wrapped by 'Annotated'
        if param.default is inspect.Parameter.empty and isinstance(param.annotation, type(None)):
            raise InvalidAPIParametersModel(f"Type hint or Annotated must be added: {param.name}")

        param_info = Parameter(
            name=name,
            model=param.annotation,
            default=param.default,
        )

        value = await extract_param_value(request, param_info)
        handler_params.add(name, value)

    response = await handler(**handler_params.get_all())

    if not isinstance(response, BaseModel):
        raise InvalidAPIParametersModel(f"Only Pydantic Response can be handle: {type(response)}")

    return web.json_response(response.model_dump(mode="json"))


def pydantic_api_handler(handler):
    @functools.wraps(handler)
    async def wrapped(request: web.Request, *args, **kwargs) -> web.Response:
        return await pydantic_handler(request, handler)

    return wrapped


"""
This decorator processes HTTP request parameters using Pydantic models.
It supports four types of parameters:

1. Request Body (automatically parsed as JSON/YAML):
    @pydantic_api_handler
    async def handler(user: UserModel):  # UserModel is a Pydantic model
        return Response(user=user)

2. Query Parameters:
    @pydantic_api_handler
    async def handler(query: QueryModel = QueryParam(QueryModel)):
        return Response(query=query)

3. Headers:
    @pydantic_api_handler
    async def handler(headers: HeaderModel = HeaderParam(HeaderModel)):
        return Response(headers=headers)

4. Path Parameters:
    @pydantic_api_handler
    async def handler(path: PathModel = PathParam(PathModel)):
        return Response(path=path)

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
    async def handler(auth: AuthMiddlewareParam):  # No default value
        return Response(user_id=auth.user_id)

6. Multiple Parameters:
    @pydantic_api_handler
    async def handler(
        user: UserModel,  # body
        query: QueryModel = QueryParam(QueryModel),  # query parameters
        headers: HeaderModel = HeaderParam(HeaderModel),  # headers
        auth: AuthMiddleware,  # middleware parameter
    ):
        return Response(user=user, query=query, headers=headers, user_id=auth.user_id)

Note:
- All parameters must have type hints or wrapped by Annotated
- Response must be a Pydantic model
- Request body is parsed from JSON by default, or from YAML if content-type is 'text/yaml'
- MiddlewareParam classes must implement the from_request classmethod
"""
