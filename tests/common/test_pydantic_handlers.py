from typing import Optional, Self

import pytest
from aiohttp import web
from pydantic import BaseModel, Field

from ai.backend.common.pydantic_handlers import (
    BaseResponse,
    BodyParam,
    HeaderParam,
    MiddlewareParam,
    PathParam,
    QueryParam,
    pydantic_api_handler,
)


class PostUserModel(BaseModel):
    name: str
    age: int


class PostUserResponse(BaseModel):
    name: str
    age: int


@pytest.mark.asyncio
async def test_body_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(user: BodyParam[PostUserModel]):
        parsed_user = user.parsed
        return BaseResponse(
            status_code=200, data=PostUserResponse(name=parsed_user.name, age=parsed_user.age)
        )

    app = web.Application()
    app.router.add_route("POST", "/test", handler)

    client = await aiohttp_client(app)

    test_data = {"name": "John", "age": 30}
    resp = await client.post("/test", json=test_data)

    assert resp.status == 200
    data = await resp.json()
    assert data["name"] == "John"
    assert data["age"] == 30


class SearchQueryModel(BaseModel):
    search: str
    page: Optional[int] = Field(default=1)


class SearchQueryResponse(BaseModel):
    search: str
    page: Optional[int] = Field(default=1)


@pytest.mark.asyncio
async def test_query_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(query: QueryParam[SearchQueryModel]):
        parsed_query = query.parsed
        return BaseResponse(
            data=SearchQueryResponse(search=parsed_query.search, page=parsed_query.page)
        )

    app = web.Application()
    app.router.add_get("/test", handler)

    client = await aiohttp_client(app)
    resp = await client.get("/test?search=test&page=2")

    assert resp.status == 200
    data = await resp.json()
    assert data["search"] == "test"
    assert data["page"] == 2


class AuthHeaderModel(BaseModel):
    authorization: str


class AuthHeaderResponse(BaseModel):
    authorization: str


@pytest.mark.asyncio
async def test_header_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(headers: HeaderParam[AuthHeaderModel]):
        parsed_headers = headers.parsed
        return BaseResponse(data=AuthHeaderResponse(authorization=parsed_headers.authorization))

    app = web.Application()
    app.router.add_get("/test", handler)

    client = await aiohttp_client(app)
    headers = {"Authorization": "Bearer token123"}
    resp = await client.get("/test", headers=headers)

    assert resp.status == 200
    data = await resp.json()
    assert data["authorization"] == "Bearer token123"


class UserPathModel(BaseModel):
    user_id: str


class UserPathResponse(BaseModel):
    user_id: str


@pytest.mark.asyncio
async def test_path_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(path: PathParam[UserPathModel]):
        parsed_path = path.parsed
        return BaseResponse(data=UserPathResponse(user_id=parsed_path.user_id))

    app = web.Application()
    app.router.add_get("/test/{user_id}", handler)

    client = await aiohttp_client(app)
    resp = await client.get("/test/123")

    assert resp.status == 200
    data = await resp.json()
    assert data["user_id"] == "123"


class AuthInfo(MiddlewareParam):
    is_authorized: bool = Field(default=False)

    @classmethod
    def from_request(cls, request: web.Request) -> Self:
        return cls(is_authorized=request.get("is_authorized", False))


class AuthResponse(BaseModel):
    is_authorized: bool = Field(default=False)


@pytest.mark.asyncio
async def test_middleware_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(auth: AuthInfo):
        return BaseResponse(data=AuthResponse(is_authorized=auth.is_authorized))

    @web.middleware
    async def auth_middleware(request, handler):
        request["is_authorized"] = True
        return await handler(request)

    app = web.Application()
    app.middlewares.append(auth_middleware)
    app.router.add_get("/test", handler)
    client = await aiohttp_client(app)

    resp = await client.get("/test")

    assert resp.status == 200
    data = await resp.json()
    assert data["is_authorized"]


@pytest.mark.asyncio
async def test_middleware_parameter_invalid_type(aiohttp_client):
    @pydantic_api_handler
    async def handler(auth: AuthInfo):
        return BaseResponse(data=AuthResponse(is_authorized=auth.is_authorized))

    @web.middleware
    async def broken_auth_middleware(request, handler):
        request["is_authorized"] = "not_a_boolean"
        return await handler(request)

    app = web.Application()
    app.middlewares.append(broken_auth_middleware)
    app.router.add_get("/test", handler)
    client = await aiohttp_client(app)

    resp = await client.get("/test")
    assert resp.status == 500

    error_data = await resp.json()
    assert error_data["type"] == "https://api.backend.ai/probs/internal-server-error"
    assert "Middleware parameter parsing failed" in error_data["title"]


class MiddlewareTestModel(MiddlewareParam):
    is_authorized: bool

    @classmethod
    def from_request(cls, request: web.Request) -> Self:
        return cls(is_authorized=request.get("is_authorized", False))


class CreateUserModel(BaseModel):
    user_name: str


class SearchParamModel(BaseModel):
    query: str


class CombinedResponse(BaseModel):
    user_name: str
    query: str
    is_authorized: bool


@pytest.mark.asyncio
async def test_multiple_parameters(aiohttp_client):
    @pydantic_api_handler
    async def handler(
        body: BodyParam[CreateUserModel],
        auth: MiddlewareTestModel,
        query: QueryParam[SearchParamModel],
    ):
        parsed_body = body.parsed
        parsed_query = query.parsed

        return BaseResponse(
            data=CombinedResponse(
                user_name=parsed_body.user_name,
                query=parsed_query.query,
                is_authorized=auth.is_authorized,
            )
        )

    @web.middleware
    async def auth_middleware(request, handler):
        request["is_authorized"] = True
        return await handler(request)

    app = web.Application()
    app.middlewares.append(auth_middleware)
    app.router.add_post("/test", handler)

    client = await aiohttp_client(app)
    test_data = {"user_name": "John"}
    resp = await client.post("/test?query=yes", json=test_data)

    assert resp.status == 200
    data = await resp.json()
    assert data["user_name"] == "John"
    assert data["query"] == "yes"
    assert data["is_authorized"]


class RegisterUserModel(BaseModel):
    name: str
    age: int


class RegisterUserResponse(BaseModel):
    name: str
    age: int


@pytest.mark.asyncio
async def test_invalid_body(aiohttp_client):
    @pydantic_api_handler
    async def handler(user: BodyParam[RegisterUserModel]):
        test_user = user.parsed
        return BaseResponse(data=RegisterUserResponse(name=test_user.name, age=test_user.age))

    app = web.Application()
    app.router.add_post("/test", handler)
    client = await aiohttp_client(app)

    test_data = {"name": "John"}  # age field missing
    error_response = await client.post("/test", json=test_data)
    assert error_response.status == 400


class ProductSearchModel(BaseModel):
    search: str
    page: Optional[int] = Field(default=1)


class ProductSearchResponse(BaseModel):
    search: str
    page: Optional[int] = Field(default=1)


@pytest.mark.asyncio
async def test_invalid_query_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(query: QueryParam[ProductSearchModel]):
        parsed_query = query.parsed
        return BaseResponse(
            data=ProductSearchResponse(search=parsed_query.search, page=parsed_query.page)
        )

    app = web.Application()
    app.router.add_get("/test", handler)
    client = await aiohttp_client(app)
    error_response = await client.get("/test")  # request with no query parameter
    assert error_response.status == 400  # InvalidAPIParameters Error raised
