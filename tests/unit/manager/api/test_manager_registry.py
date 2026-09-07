"""Route-level authorization tests for the manager API registry."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp_cors
import pytest
from aiohttp.test_utils import make_mocked_request

from ai.backend.manager.api.rest.manager.handler import ManagerHandler
from ai.backend.manager.api.rest.manager.registry import register_manager_api_routes
from ai.backend.manager.api.rest.types import CORSOptions, RouteDeps, WebRequestHandler
from ai.backend.manager.errors.common import GenericForbidden


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
def registered_handlers(cors_options: CORSOptions) -> dict[tuple[str, str], WebRequestHandler]:
    processors = MagicMock()
    processors.get_announcement.run = AsyncMock(
        return_value=MagicMock(enabled=True, message="hello")
    )
    route_deps = RouteDeps(
        cors_options=cors_options,
        read_status_mw=MagicMock(),
        all_status_mw=MagicMock(),
    )
    reg = register_manager_api_routes(ManagerHandler(manager_admin=processors), route_deps)
    return {
        (route.method, route.resource.canonical): route.handler  # type: ignore[union-attr]
        for route in reg.app.router.routes()
    }


class TestAnnouncementRouteAuth:
    async def test_get_allows_non_superadmin(
        self, registered_handlers: dict[tuple[str, str], WebRequestHandler]
    ) -> None:
        request = make_mocked_request("GET", "/announcement")
        request["is_authorized"] = True
        request["is_superadmin"] = False

        response = await registered_handlers[("GET", "/announcement")](request)

        assert response.status == 200

    async def test_post_rejects_non_superadmin(
        self, registered_handlers: dict[tuple[str, str], WebRequestHandler]
    ) -> None:
        request = make_mocked_request("POST", "/announcement")
        request["is_authorized"] = True
        request["is_superadmin"] = False

        with pytest.raises(GenericForbidden):
            await registered_handlers[("POST", "/announcement")](request)
