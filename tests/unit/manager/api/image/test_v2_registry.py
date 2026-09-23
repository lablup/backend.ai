from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from aiohttp import web

from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.image.handler import V2ImageHandler
from ai.backend.manager.api.rest.v2.image.registry import register_v2_image_routes


@pytest.fixture
def v2_image_routes() -> list[web.AbstractRoute]:
    route_deps = MagicMock(spec=RouteDeps)
    route_deps.cors_options = {}
    registry = register_v2_image_routes(V2ImageHandler(adapter=MagicMock()), route_deps)
    return [route for route in registry.app.router.routes() if route.method != "OPTIONS"]


class TestV2ImageRouteAuth:
    def test_every_route_requires_auth(self, v2_image_routes: list[web.AbstractRoute]) -> None:
        unauthenticated = [
            f"{route.method} {route.resource.canonical if route.resource else ''}"
            for route in v2_image_routes
            if not getattr(route.handler, "_backend_attrs", {}).get("auth_required", False)
        ]
        assert v2_image_routes
        assert unauthenticated == []
