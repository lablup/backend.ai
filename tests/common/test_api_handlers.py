from http import HTTPStatus
from typing import Optional, Self

import pytest
from aiohttp import web
from pydantic import Field

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseRequestModel,
    BaseResponseModel,
    BodyParam,
    HeaderParam,
    MiddlewareParam,
    PathParam,
    QueryParam,
    api_handler,
)


class TestEmptyResponseModel(BaseResponseModel):
    status: str
    version: str


class TestEmptyHandler:
    @api_handler
    async def handle_empty(self) -> APIResponse:
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestEmptyResponseModel(status="success", version="1.0.0"),
        )


@pytest.mark.asyncio
async def test_empty_parameter_handler_in_class(aiohttp_client):
    handler = TestEmptyHandler()
    app = web.Application()
    app.router.add_get("/system", handler.handle_empty)

    client = await aiohttp_client(app)
    resp = await client.get("/system")

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["status"] == "success"
    assert data["version"] == "1.0.0"


class TestUserRequestModel(BaseRequestModel):
    username: str
    email: str
    age: int


class TestSearchParamsModel(BaseRequestModel):
    keyword: str
    category: Optional[str] = Field(default="all")
    limit: Optional[int] = Field(default=10)


class TestCombinedResponseModel(BaseResponseModel):
    user_info: dict
    search_info: dict
    timestamp: str


class CombinedParamsHandler:
    @api_handler
    async def handle_combined(
        self, user: BodyParam[TestUserRequestModel], search: QueryParam[TestSearchParamsModel]
    ) -> APIResponse:
        parsed_user = user.parsed
        parsed_search = search.parsed

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestCombinedResponseModel(
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
    handler = CombinedParamsHandler()
    app = web.Application()
    app.router.add_post("/users/search", handler.handle_combined)

    client = await aiohttp_client(app)

    test_user_data = {"username": "john_doe", "email": "john@example.com", "age": 30}

    resp = await client.post(
        "/users/search?keyword=python&category=programming&limit=20", json=test_user_data
    )

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    assert data["user_info"]["username"] == "john_doe"
    assert data["user_info"]["email"] == "john@example.com"
    assert data["user_info"]["age"] == 30

    assert data["search_info"]["keyword"] == "python"
    assert data["search_info"]["category"] == "programming"
    assert data["search_info"]["limit"] == 20


class TestMessageResponse(BaseResponseModel):
    message: str


class TestMessageHandler:
    @api_handler
    async def handle_message(self) -> APIResponse:
        return APIResponse.build(
            status_code=HTTPStatus.OK, response_model=TestMessageResponse(message="test")
        )


@pytest.mark.asyncio
async def test_empty_parameter(aiohttp_client):
    handler = TestMessageHandler()
    app = web.Application()
    app.router.add_route("GET", "/test", handler.handle_message)

    client = await aiohttp_client(app)
    resp = await client.get("/test")

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["message"] == "test"


class TestPostUserModel(BaseRequestModel):
    name: str
    age: int


class TestPostUserResponse(BaseResponseModel):
    name: str
    age: int


class TestPostUserHandler:
    @api_handler
    async def handle_user(self, user: BodyParam[TestPostUserModel]) -> APIResponse:
        parsed_user = user.parsed
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestPostUserResponse(name=parsed_user.name, age=parsed_user.age),
        )


@pytest.mark.asyncio
async def test_body_parameter(aiohttp_client):
    handler = TestPostUserHandler()
    app = web.Application()
    app.router.add_route("POST", "/test", handler.handle_user)

    client = await aiohttp_client(app)
    test_data = {"name": "John", "age": 30}
    resp = await client.post("/test", json=test_data)

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["name"] == "John"
    assert data["age"] == 30


class TestSearchQueryModel(BaseRequestModel):
    search: str
    page: Optional[int] = Field(default=1)


class TestSearchQueryResponse(BaseResponseModel):
    search: str
    page: Optional[int] = Field(default=1)


class TestSearchQueryHandler:
    @api_handler
    async def handle_search(self, query: QueryParam[TestSearchQueryModel]) -> APIResponse:
        parsed_query = query.parsed
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestSearchQueryResponse(
                search=parsed_query.search, page=parsed_query.page
            ),
        )


@pytest.mark.asyncio
async def test_query_parameter(aiohttp_client):
    handler = TestSearchQueryHandler()
    app = web.Application()
    app.router.add_get("/test", handler.handle_search)

    client = await aiohttp_client(app)
    resp = await client.get("/test?search=test&page=2")

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["search"] == "test"
    assert data["page"] == 2


class TestAuthHeaderModel(BaseRequestModel):
    authorization: str


class TestAuthHeaderResponse(BaseResponseModel):
    authorization: str


class TestAuthHeaderHandler:
    @api_handler
    async def handle_auth(self, headers: HeaderParam[TestAuthHeaderModel]) -> APIResponse:
        parsed_headers = headers.parsed
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestAuthHeaderResponse(authorization=parsed_headers.authorization),
        )


@pytest.mark.asyncio
async def test_header_parameter(aiohttp_client):
    handler = TestAuthHeaderHandler()
    app = web.Application()
    app.router.add_get("/test", handler.handle_auth)

    client = await aiohttp_client(app)
    headers = {"Authorization": "Bearer token123"}
    resp = await client.get("/test", headers=headers)

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["authorization"] == "Bearer token123"


class TestUserPathModel(BaseRequestModel):
    user_id: str


class TestUserPathResponse(BaseResponseModel):
    user_id: str


class TestUserPathHandler:
    @api_handler
    async def handle_path(self, path: PathParam[TestUserPathModel]) -> APIResponse:
        parsed_path = path.parsed
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestUserPathResponse(user_id=parsed_path.user_id),
        )


@pytest.mark.asyncio
async def test_path_parameter(aiohttp_client):
    handler = TestUserPathHandler()
    app = web.Application()
    app.router.add_get("/test/{user_id}", handler.handle_path)

    client = await aiohttp_client(app)
    resp = await client.get("/test/123")

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["user_id"] == "123"


class TestAuthInfo(MiddlewareParam):
    is_authorized: bool = Field(default=False)

    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(is_authorized=request.get("is_authorized", False))


class TestAuthResponse(BaseResponseModel):
    is_authorized: bool = Field(default=False)


class TestAuthHandler:
    @api_handler
    async def handle_middleware_auth(self, auth: TestAuthInfo) -> APIResponse:
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestAuthResponse(is_authorized=auth.is_authorized),
        )


@pytest.mark.asyncio
async def test_middleware_parameter(aiohttp_client):
    handler = TestAuthHandler()

    @web.middleware
    async def auth_middleware(request, handler):
        request["is_authorized"] = True
        return await handler(request)

    app = web.Application()
    app.middlewares.append(auth_middleware)
    app.router.add_get("/test", handler.handle_middleware_auth)
    client = await aiohttp_client(app)

    resp = await client.get("/test")

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["is_authorized"]


class TestInvalidAuthHandler:
    @api_handler
    async def handle_invalid_auth(self, auth: TestAuthInfo) -> APIResponse:
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestAuthResponse(is_authorized=auth.is_authorized),
        )


@pytest.mark.asyncio
async def test_middleware_parameter_invalid_type(aiohttp_client):
    handler = TestInvalidAuthHandler()

    @web.middleware
    async def broken_auth_middleware(request, handler):
        request["is_authorized"] = "not_a_boolean"
        return await handler(request)

    app = web.Application()
    app.middlewares.append(broken_auth_middleware)
    app.router.add_get("/test", handler.handle_invalid_auth)
    client = await aiohttp_client(app)

    resp = await client.get("/test")
    assert resp.status == HTTPStatus.INTERNAL_SERVER_ERROR

    error_data = await resp.json()
    assert error_data["type"] == "https://api.backend.ai/probs/internal-server-error"
    assert "Middleware parameter parsing failed" in error_data["title"]


class TestMiddlewareModel(MiddlewareParam):
    is_authorized: bool

    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(is_authorized=request.get("is_authorized", False))


class TestCreateUserModel(BaseRequestModel):
    user_name: str


class TestSearchParamModel(BaseRequestModel):
    query: str


class TestCombinedResponse(BaseResponseModel):
    user_name: str
    query: str
    is_authorized: bool


class TestMultipleParamsHandler:
    @api_handler
    async def handle_multiple(
        self,
        body: BodyParam[TestCreateUserModel],
        auth: TestMiddlewareModel,
        query: QueryParam[TestSearchParamModel],
    ) -> APIResponse:
        parsed_body = body.parsed
        parsed_query = query.parsed

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestCombinedResponse(
                user_name=parsed_body.user_name,
                query=parsed_query.query,
                is_authorized=auth.is_authorized,
            ),
        )


@pytest.mark.asyncio
async def test_multiple_parameters(aiohttp_client):
    handler = TestMultipleParamsHandler()

    @web.middleware
    async def auth_middleware(request, handler):
        request["is_authorized"] = True
        return await handler(request)

    app = web.Application()
    app.middlewares.append(auth_middleware)
    app.router.add_post("/test", handler.handle_multiple)

    client = await aiohttp_client(app)
    test_data = {"user_name": "John"}
    resp = await client.post("/test?query=yes", json=test_data)

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["user_name"] == "John"
    assert data["query"] == "yes"
    assert data["is_authorized"]


class TestRegisterUserModel(BaseRequestModel):
    name: str
    age: int


class TestRegisterUserResponse(BaseResponseModel):
    name: str
    age: int


class TestRegisterUserHandler:
    @api_handler
    async def handle_register(self, user: BodyParam[TestRegisterUserModel]) -> APIResponse:
        test_user = user.parsed
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestRegisterUserResponse(name=test_user.name, age=test_user.age),
        )


@pytest.mark.asyncio
async def test_invalid_body(aiohttp_client):
    handler = TestRegisterUserHandler()
    app = web.Application()
    app.router.add_post("/test", handler.handle_register)
    client = await aiohttp_client(app)

    test_data = {"name": "John"}  # age field missing
    error_response = await client.post("/test", json=test_data)
    assert error_response.status == HTTPStatus.BAD_REQUEST


class TestProductSearchModel(BaseRequestModel):
    search: str
    page: Optional[int] = Field(default=1)


class TestProductSearchResponse(BaseResponseModel):
    search: str
    page: Optional[int] = Field(default=1)


class TestProductSearchHandler:
    @api_handler
    async def handle_product_search(self, query: QueryParam[TestProductSearchModel]) -> APIResponse:
        parsed_query = query.parsed
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=TestProductSearchResponse(
                search=parsed_query.search, page=parsed_query.page
            ),
        )


@pytest.mark.asyncio
async def test_invalid_query_parameter(aiohttp_client):
    handler = TestProductSearchHandler()
    app = web.Application()
    app.router.add_get("/test", handler.handle_product_search)
    client = await aiohttp_client(app)
    # request with no query parameter
    error_response = await client.get("/test")
    assert error_response.status == HTTPStatus.BAD_REQUEST  # InvalidAPIParameters Error raised
