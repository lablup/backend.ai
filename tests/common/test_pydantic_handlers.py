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


class TestEmptyResponseModel(BaseModel):
    status: str
    version: str


class TestEmptyHandlerClass:
    @pydantic_api_handler
    async def handle_empty(self) -> BaseResponse:
        return BaseResponse(
            status_code=200, data=TestEmptyResponseModel(status="success", version="1.0.0")
        )


@pytest.mark.asyncio
async def test_empty_parameter_handler_in_class(aiohttp_client):
    handler = TestEmptyHandlerClass()
    app = web.Application()
    app.router.add_get("/system", handler.handle_empty)

    client = await aiohttp_client(app)
    resp = await client.get("/system")

    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "success"
    assert data["version"] == "1.0.0"


class TestUserRequestModel(BaseModel):
    username: str
    email: str
    age: int


class TestSearchParamsModel(BaseModel):
    keyword: str
    category: Optional[str] = Field(default="all")
    limit: Optional[int] = Field(default=10)


class TestCombinedResponseModel(BaseModel):
    user_info: dict
    search_info: dict
    timestamp: str


class CombinedParamsHandlerClass:
    @pydantic_api_handler
    async def handle_combined(
        self, user: BodyParam[TestUserRequestModel], search: QueryParam[TestSearchParamsModel]
    ) -> BaseResponse:
        parsed_user = user.parsed
        parsed_search = search.parsed

        return BaseResponse(
            status_code=200,
            data=TestCombinedResponseModel(
                user_info={
                    "username": parsed_user.username,
                    "email": parsed_user.email,
                    "age": parsed_user.age,
                },
                search_info={
                    "keyword": parsed_search.keyword,
                    "category": parsed_search.category,
                    "limit": parsed_search.limit,
                },
                timestamp="2024-01-31T00:00:00Z",
            ),
        )


@pytest.mark.asyncio
async def test_combined_parameters_handler_in_class(aiohttp_client):
    handler = CombinedParamsHandlerClass()
    app = web.Application()
    app.router.add_post("/users/search", handler.handle_combined)

    client = await aiohttp_client(app)

    test_user_data = {"username": "john_doe", "email": "john@example.com", "age": 30}

    resp = await client.post(
        "/users/search?keyword=python&category=programming&limit=20", json=test_user_data
    )

    assert resp.status == 200
    data = await resp.json()

    assert data["user_info"]["username"] == "john_doe"
    assert data["user_info"]["email"] == "john@example.com"
    assert data["user_info"]["age"] == 30

    assert data["search_info"]["keyword"] == "python"
    assert data["search_info"]["category"] == "programming"
    assert data["search_info"]["limit"] == 20


class TestMessageResponse(BaseModel):
    message: str


@pytest.mark.asyncio
async def test_empty_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler() -> BaseResponse:
        return BaseResponse(status_code=200, data=TestMessageResponse(message="test"))

    app = web.Application()
    app.router.add_route("GET", "/test", handler)

    client = await aiohttp_client(app)

    resp = await client.get("/test")

    assert resp.status == 200
    data = await resp.json()
    assert data["message"] == "test"


class TestPostUserModel(BaseModel):
    name: str
    age: int


class TestPostUserResponse(BaseModel):
    name: str
    age: int


@pytest.mark.asyncio
async def test_body_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(user: BodyParam[TestPostUserModel]) -> BaseResponse:
        parsed_user = user.parsed
        return BaseResponse(
            status_code=200, data=TestPostUserResponse(name=parsed_user.name, age=parsed_user.age)
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


class TestSearchQueryModel(BaseModel):
    search: str
    page: Optional[int] = Field(default=1)


class TestSearchQueryResponse(BaseModel):
    search: str
    page: Optional[int] = Field(default=1)


@pytest.mark.asyncio
async def test_query_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(query: QueryParam[TestSearchQueryModel]) -> BaseResponse:
        parsed_query = query.parsed
        return BaseResponse(
            status_code=200,
            data=TestSearchQueryResponse(search=parsed_query.search, page=parsed_query.page),
        )

    app = web.Application()
    app.router.add_get("/test", handler)

    client = await aiohttp_client(app)
    resp = await client.get("/test?search=test&page=2")

    assert resp.status == 200
    data = await resp.json()
    assert data["search"] == "test"
    assert data["page"] == 2


class TestAuthHeaderModel(BaseModel):
    authorization: str


class TestAuthHeaderResponse(BaseModel):
    authorization: str


@pytest.mark.asyncio
async def test_header_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(headers: HeaderParam[TestAuthHeaderModel]) -> BaseResponse:
        parsed_headers = headers.parsed
        return BaseResponse(
            status_code=200, data=TestAuthHeaderResponse(authorization=parsed_headers.authorization)
        )

    app = web.Application()
    app.router.add_get("/test", handler)

    client = await aiohttp_client(app)
    headers = {"Authorization": "Bearer token123"}
    resp = await client.get("/test", headers=headers)

    assert resp.status == 200
    data = await resp.json()
    assert data["authorization"] == "Bearer token123"


class TestUserPathModel(BaseModel):
    user_id: str


class TestUserPathResponse(BaseModel):
    user_id: str


@pytest.mark.asyncio
async def test_path_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(path: PathParam[TestUserPathModel]) -> BaseResponse:
        parsed_path = path.parsed
        return BaseResponse(status_code=200, data=TestUserPathResponse(user_id=parsed_path.user_id))

    app = web.Application()
    app.router.add_get("/test/{user_id}", handler)

    client = await aiohttp_client(app)
    resp = await client.get("/test/123")

    assert resp.status == 200
    data = await resp.json()
    assert data["user_id"] == "123"


class TestAuthInfo(MiddlewareParam):
    is_authorized: bool = Field(default=False)

    @classmethod
    def from_request(cls, request: web.Request) -> Self:
        return cls(is_authorized=request.get("is_authorized", False))


class TestAuthResponse(BaseModel):
    is_authorized: bool = Field(default=False)


@pytest.mark.asyncio
async def test_middleware_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(auth: TestAuthInfo) -> BaseResponse:
        return BaseResponse(
            status_code=200, data=TestAuthResponse(is_authorized=auth.is_authorized)
        )

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
    async def handler(auth: TestAuthInfo) -> BaseResponse:
        return BaseResponse(
            status_code=200, data=TestAuthResponse(is_authorized=auth.is_authorized)
        )

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


class TestMiddlewareModel(MiddlewareParam):
    is_authorized: bool

    @classmethod
    def from_request(cls, request: web.Request) -> Self:
        return cls(is_authorized=request.get("is_authorized", False))


class TestCreateUserModel(BaseModel):
    user_name: str


class TestSearchParamModel(BaseModel):
    query: str


class TestCombinedResponse(BaseModel):
    user_name: str
    query: str
    is_authorized: bool


@pytest.mark.asyncio
async def test_multiple_parameters(aiohttp_client):
    @pydantic_api_handler
    async def handler(
        body: BodyParam[TestCreateUserModel],
        auth: TestMiddlewareModel,
        query: QueryParam[TestSearchParamModel],
    ) -> BaseResponse:
        parsed_body = body.parsed
        parsed_query = query.parsed

        return BaseResponse(
            status_code=200,
            data=TestCombinedResponse(
                user_name=parsed_body.user_name,
                query=parsed_query.query,
                is_authorized=auth.is_authorized,
            ),
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


class TestRegisterUserModel(BaseModel):
    name: str
    age: int


class TestRegisterUserResponse(BaseModel):
    name: str
    age: int


@pytest.mark.asyncio
async def test_invalid_body(aiohttp_client):
    @pydantic_api_handler
    async def handler(user: BodyParam[TestRegisterUserModel]) -> BaseResponse:
        test_user = user.parsed
        return BaseResponse(
            status_code=200, data=TestRegisterUserResponse(name=test_user.name, age=test_user.age)
        )

    app = web.Application()
    app.router.add_post("/test", handler)
    client = await aiohttp_client(app)

    test_data = {"name": "John"}  # age field missing
    error_response = await client.post("/test", json=test_data)
    assert error_response.status == 400


class TestProductSearchModel(BaseModel):
    search: str
    page: Optional[int] = Field(default=1)


class TestProductSearchResponse(BaseModel):
    search: str
    page: Optional[int] = Field(default=1)


@pytest.mark.asyncio
async def test_invalid_query_parameter(aiohttp_client):
    @pydantic_api_handler
    async def handler(query: QueryParam[TestProductSearchModel]) -> BaseResponse:
        parsed_query = query.parsed
        return BaseResponse(
            status_code=200,
            data=TestProductSearchResponse(search=parsed_query.search, page=parsed_query.page),
        )

    app = web.Application()
    app.router.add_get("/test", handler)
    client = await aiohttp_client(app)
    error_response = await client.get("/test")  # request with no query parameter
    assert error_response.status == 400  # InvalidAPIParameters Error raised
