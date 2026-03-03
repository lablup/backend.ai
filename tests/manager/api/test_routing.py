"""Unit tests for RouteRegistry."""

from __future__ import annotations

import asyncio
import functools
import json
from collections.abc import Awaitable, Callable
from typing import Self
from unittest.mock import AsyncMock, MagicMock

import aiohttp_cors
import pytest
from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseRequestModel,
    BaseResponseModel,
    BodyParam,
    MiddlewareParam,
)
from ai.backend.manager.api.rest.middleware.auth import (
    admin_required,
    auth_middleware,
    auth_required,
    superadmin_required,
)
from ai.backend.manager.api.rest.routing import (
    RouteRegistry,
    _apply_route_middlewares,
    _wrap_api_handler,
)
from ai.backend.manager.api.rest.types import CORSOptions


@pytest.fixture
def cors_options() -> CORSOptions:
    return {
        "*": aiohttp_cors.ResourceOptions(  # type: ignore[no-untyped-call]
            allow_credentials=False,
            expose_headers="*",
            allow_headers="*",
        ),
    }


@pytest.fixture
def app() -> web.Application:
    return web.Application()


@pytest.fixture
def registry(app: web.Application, cors_options: CORSOptions) -> RouteRegistry:
    return RouteRegistry(app, cors_options)


def _make_middleware(
    name: str,
    call_order: list[str],
) -> Callable[
    [Callable[..., Awaitable[web.StreamResponse]]],
    Callable[..., Awaitable[web.StreamResponse]],
]:
    def middleware(
        handler: Callable[..., Awaitable[web.StreamResponse]],
    ) -> Callable[..., Awaitable[web.StreamResponse]]:
        @functools.wraps(handler)
        async def wrapped(request: web.Request) -> web.StreamResponse:
            call_order.append(name)
            return await handler(request)

        return wrapped

    return middleware


class DummyResponse(BaseResponseModel):
    handler: str


async def _dummy_handler() -> APIResponse:
    return APIResponse.build(status_code=200, response_model=DummyResponse(handler="dummy"))


async def _another_handler() -> APIResponse:
    return APIResponse.build(status_code=200, response_model=DummyResponse(handler="another"))


async def _raw_web_handler(request: web.Request) -> web.Response:
    """Raw web handler for testing _apply_route_middlewares directly."""
    return web.json_response({"handler": "raw"})


class TestRouteRegistryInit:
    def test_stores_app_reference(self, app: web.Application, registry: RouteRegistry) -> None:
        assert registry.app is app

    def test_cors_is_configured(self, registry: RouteRegistry) -> None:
        assert registry.cors is not None
        assert isinstance(registry.cors, aiohttp_cors.CorsConfig)

    def test_no_default_middlewares(self, registry: RouteRegistry) -> None:
        assert registry.middlewares == []

    def test_registry_level_middlewares_stored(
        self, app: web.Application, cors_options: CORSOptions
    ) -> None:
        call_order: list[str] = []
        mw = _make_middleware("reg", call_order)
        reg = RouteRegistry(app, cors_options, middlewares=[mw])
        assert reg.middlewares == [mw]


class TestRouteRegistryAdd:
    def test_adds_route_to_app(self, registry: RouteRegistry) -> None:
        registry.add("GET", "/test", _dummy_handler)

        routes = list(registry.app.router.routes())
        # aiohttp_cors adds an OPTIONS route alongside the main route
        method_routes = [r for r in routes if r.method == "GET"]
        assert len(method_routes) == 1
        assert method_routes[0].resource is not None

    def test_adds_multiple_routes(self, registry: RouteRegistry) -> None:
        registry.add("GET", "/first", _dummy_handler)
        registry.add("POST", "/second", _another_handler)

        routes = list(registry.app.router.routes())
        get_routes = [r for r in routes if r.method == "GET"]
        post_routes = [r for r in routes if r.method == "POST"]
        assert len(get_routes) == 1
        assert len(post_routes) == 1

    def test_returns_route_object(self, registry: RouteRegistry) -> None:
        route = registry.add("GET", "/test", _dummy_handler)
        assert isinstance(route, web.AbstractRoute)

    def test_route_without_middleware(self, registry: RouteRegistry) -> None:
        route = registry.add("GET", "/test", _dummy_handler)
        # Handler is always wrapped by _wrap_api_handler
        assert id(route.handler) != id(_dummy_handler)

    def test_route_with_empty_middleware_list(self, registry: RouteRegistry) -> None:
        route = registry.add("GET", "/test", _dummy_handler, middlewares=[])
        assert id(route.handler) != id(_dummy_handler)

    def test_registry_middleware_applied_to_all_routes(
        self, app: web.Application, cors_options: CORSOptions
    ) -> None:
        call_order: list[str] = []
        mw = _make_middleware("reg", call_order)
        reg = RouteRegistry(app, cors_options, middlewares=[mw])

        route = reg.add("GET", "/test", _dummy_handler)
        # Handler should be wrapped by registry-level middleware
        assert id(route.handler) != id(_dummy_handler)

    def test_registry_plus_route_middlewares_combined(
        self, app: web.Application, cors_options: CORSOptions
    ) -> None:
        call_order: list[str] = []
        reg_mw = _make_middleware("registry", call_order)
        route_mw = _make_middleware("route", call_order)
        reg = RouteRegistry(app, cors_options, middlewares=[reg_mw])

        reg.add("GET", "/test", _dummy_handler, middlewares=[route_mw])

        # Verify execution order: registry first, then route
        wrapped = _apply_route_middlewares(_raw_web_handler, [reg_mw, route_mw])
        mock_request = MagicMock(spec=web.Request)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(wrapped(mock_request))
        finally:
            loop.close()
        assert call_order == ["registry", "route"]


class TestRouteMiddlewareChaining:
    def test_single_middleware_wraps_handler(self, registry: RouteRegistry) -> None:
        call_order: list[str] = []
        middleware_a = _make_middleware("a", call_order)

        route = registry.add("GET", "/test", _dummy_handler, middlewares=[middleware_a])
        # Handler should be wrapped (not the original)
        assert id(route.handler) != id(_dummy_handler)

    def test_middleware_order_matches_decorator_stacking(self, registry: RouteRegistry) -> None:
        """First middleware in list = outermost wrapper (executed first)."""
        call_order: list[str] = []
        mw_first = _make_middleware("first", call_order)
        mw_second = _make_middleware("second", call_order)

        registry.add(
            "GET",
            "/test",
            _dummy_handler,
            middlewares=[mw_first, mw_second],
        )

        # Verify ordering via _apply_route_middlewares directly
        call_order.clear()
        wrapped = _apply_route_middlewares(_raw_web_handler, [mw_first, mw_second])

        mock_request = MagicMock(spec=web.Request)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(wrapped(mock_request))
        finally:
            loop.close()

        # "first" should execute before "second"
        assert call_order == ["first", "second"]

    def test_three_middleware_chain(self, registry: RouteRegistry) -> None:
        """Verify correct ordering with three middlewares."""
        call_order: list[str] = []

        wrapped = _apply_route_middlewares(
            _raw_web_handler,
            [
                _make_middleware("a", call_order),
                _make_middleware("b", call_order),
                _make_middleware("c", call_order),
            ],
        )

        mock_request = MagicMock(spec=web.Request)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(wrapped(mock_request))
        finally:
            loop.close()

        assert call_order == ["a", "b", "c"]


class TestApplyRouteMiddlewares:
    def test_empty_middlewares_returns_original(self) -> None:
        result = _apply_route_middlewares(_raw_web_handler, [])
        assert result is _raw_web_handler

    def test_preserves_handler_attributes(self) -> None:
        """Middleware using functools.wraps should preserve handler metadata."""

        def attr_setting_middleware(
            handler: Callable[..., Awaitable[web.StreamResponse]],
        ) -> Callable[..., Awaitable[web.StreamResponse]]:
            @functools.wraps(handler)
            async def wrapped(request: web.Request) -> web.StreamResponse:
                return await handler(request)

            return wrapped

        wrapped = _apply_route_middlewares(_raw_web_handler, [attr_setting_middleware])
        assert wrapped.__name__ == _raw_web_handler.__name__


class TestAuthMiddlewareImportability:
    """Verify auth_middleware can be imported independently from create_app()."""

    def test_auth_middleware_is_importable(self) -> None:
        assert callable(auth_middleware)

    def test_auth_decorators_are_importable(self) -> None:
        assert callable(auth_required)
        assert callable(admin_required)
        assert callable(superadmin_required)


class CreateUserRequest(BaseRequestModel):
    name: str
    email: str


class CreateUserResponse(BaseResponseModel):
    name: str
    email: str


class MockMiddlewareParam(MiddlewareParam):
    user_id: str

    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        return cls(user_id="test-user-123")


class TestRouteRegistryAutoWrapping:
    """Verify that RouteRegistry.add() always wraps handlers with _wrap_api_handler."""

    def test_handler_always_wrapped(self, registry: RouteRegistry) -> None:
        """All handlers registered via add() should be wrapped, not the original."""
        route = registry.add("GET", "/test", _dummy_handler)
        assert id(route.handler) != id(_dummy_handler)

    async def test_wrapped_handler_parses_body(self) -> None:
        """_wrap_api_handler should parse BodyParam from request JSON body."""

        async def create_user(body: BodyParam[CreateUserRequest]) -> APIResponse:
            return APIResponse.build(
                status_code=201,
                response_model=CreateUserResponse(
                    name=body.parsed.name,
                    email=body.parsed.email,
                ),
            )

        wrapped = _wrap_api_handler(create_user)

        mock_request = AsyncMock(spec=web.Request)
        mock_request.can_read_body = True
        mock_request.json = AsyncMock(return_value={"name": "Alice", "email": "alice@example.com"})

        response = await wrapped(mock_request)
        assert isinstance(response, web.Response)
        assert response.status == 201
        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        assert body["name"] == "Alice"
        assert body["email"] == "alice@example.com"

    async def test_wrapped_handler_converts_api_response(self) -> None:
        """_wrap_api_handler should convert APIResponse to web.Response with correct status and body."""

        async def health_check() -> APIResponse:
            return APIResponse.build(
                status_code=200,
                response_model=DummyResponse(handler="health"),
            )

        wrapped = _wrap_api_handler(health_check)

        mock_request = AsyncMock(spec=web.Request)
        response = await wrapped(mock_request)
        assert isinstance(response, web.Response)
        assert response.status == 200
        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        assert body["handler"] == "health"

    async def test_middleware_param_extracted(self) -> None:
        """_wrap_api_handler should call from_request() for MiddlewareParam subclasses."""

        async def get_profile(ctx: MockMiddlewareParam) -> APIResponse:
            return APIResponse.build(
                status_code=200,
                response_model=DummyResponse(handler=ctx.user_id),
            )

        wrapped = _wrap_api_handler(get_profile)

        mock_request = AsyncMock(spec=web.Request)
        response = await wrapped(mock_request)
        assert isinstance(response, web.Response)
        assert response.status == 200
        assert isinstance(response.body, bytes)
        body = json.loads(response.body)
        assert body["handler"] == "test-user-123"

    async def test_no_params_handler_works(self) -> None:
        """Handlers with no parameters should work correctly."""

        async def no_params() -> APIResponse:
            return APIResponse.build(
                status_code=204,
                response_model=DummyResponse(handler="none"),
            )

        wrapped = _wrap_api_handler(no_params)

        mock_request = AsyncMock(spec=web.Request)
        response = await wrapped(mock_request)
        assert response.status == 204
