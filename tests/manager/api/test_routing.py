"""Unit tests for RouteRegistry."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Awaitable, Callable
from unittest.mock import MagicMock

import aiohttp_cors
import pytest
from aiohttp import web

from ai.backend.manager.api.auth import (
    admin_required,
    auth_middleware,
    auth_required,
    superadmin_required,
)
from ai.backend.manager.api.routing import RouteRegistry, _apply_route_middlewares
from ai.backend.manager.api.types import CORSOptions


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


async def _dummy_handler(request: web.Request) -> web.Response:
    return web.json_response({"handler": "dummy"})


async def _another_handler(request: web.Request) -> web.Response:
    return web.json_response({"handler": "another"})


class TestRouteRegistryInit:
    def test_stores_app_reference(self, app: web.Application, registry: RouteRegistry) -> None:
        assert registry.app is app

    def test_cors_is_configured(self, registry: RouteRegistry) -> None:
        assert registry.cors is not None
        assert isinstance(registry.cors, aiohttp_cors.CorsConfig)


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
        # The handler should be the original (no wrapping)
        assert route.handler is _dummy_handler

    def test_route_with_empty_middleware_list(self, registry: RouteRegistry) -> None:
        route = registry.add("GET", "/test", _dummy_handler, middlewares=[])
        assert route.handler is _dummy_handler


class TestRouteMiddlewareChaining:
    def test_single_middleware_wraps_handler(self, registry: RouteRegistry) -> None:
        call_order: list[str] = []

        def middleware_a(
            handler: Callable[..., Awaitable[web.StreamResponse]],
        ) -> Callable[..., Awaitable[web.StreamResponse]]:
            @functools.wraps(handler)
            async def wrapped(request: web.Request) -> web.StreamResponse:
                call_order.append("a")
                return await handler(request)

            return wrapped

        route = registry.add("GET", "/test", _dummy_handler, middlewares=[middleware_a])
        # Handler should be wrapped (not the original)
        assert route.handler is not _dummy_handler

    def test_middleware_order_matches_decorator_stacking(self, registry: RouteRegistry) -> None:
        """First middleware in list = outermost wrapper (executed first)."""
        call_order: list[str] = []

        def make_middleware(
            name: str,
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

        mw_first = make_middleware("first")
        mw_second = make_middleware("second")

        registry.add(
            "GET",
            "/test",
            _dummy_handler,
            middlewares=[mw_first, mw_second],
        )

        # Verify ordering via _apply_route_middlewares directly
        call_order.clear()
        wrapped = _apply_route_middlewares(_dummy_handler, [mw_first, mw_second])

        # Create a mock request to invoke the chain
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

        def make_middleware(
            name: str,
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

        wrapped = _apply_route_middlewares(
            _dummy_handler,
            [make_middleware("a"), make_middleware("b"), make_middleware("c")],
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
        result = _apply_route_middlewares(_dummy_handler, [])
        assert result is _dummy_handler

    def test_preserves_handler_attributes(self) -> None:
        """Middleware using functools.wraps should preserve handler metadata."""

        def attr_setting_middleware(
            handler: Callable[..., Awaitable[web.StreamResponse]],
        ) -> Callable[..., Awaitable[web.StreamResponse]]:
            @functools.wraps(handler)
            async def wrapped(request: web.Request) -> web.StreamResponse:
                return await handler(request)

            return wrapped

        wrapped = _apply_route_middlewares(_dummy_handler, [attr_setting_middleware])
        assert wrapped.__name__ == _dummy_handler.__name__


class TestAuthMiddlewareImportability:
    """Verify auth_middleware can be imported independently from create_app()."""

    def test_auth_middleware_is_importable(self) -> None:
        assert callable(auth_middleware)

    def test_auth_decorators_are_importable(self) -> None:
        assert callable(auth_required)
        assert callable(admin_required)
        assert callable(superadmin_required)
