from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.typedefs import Middleware

from ai.backend.common.plugin.monitor import INCREMENT
from ai.backend.manager.api.rest.middleware.exception import build_exception_middleware


@dataclass(frozen=True)
class _RedirectCase:
    raised: web.HTTPException
    expected_status: int
    expected_location: str


class TestExceptionMiddleware:
    @pytest.fixture
    def stats_monitor(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def middleware(self, stats_monitor: AsyncMock) -> Middleware:
        config_provider = MagicMock()
        config_provider.config.debug.enabled = False
        return build_exception_middleware(
            error_monitor=AsyncMock(),
            stats_monitor=stats_monitor,
            config_provider=config_provider,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _RedirectCase(
                raised=web.HTTPFound("/elsewhere"),
                expected_status=302,
                expected_location="/elsewhere",
            ),
            _RedirectCase(
                raised=web.HTTPPermanentRedirect("/moved"),
                expected_status=308,
                expected_location="/moved",
            ),
        ],
        ids=lambda case: type(case.raised).__name__,
    )
    async def test_redirect_passes_through(
        self,
        aiohttp_client: Any,
        middleware: Middleware,
        stats_monitor: AsyncMock,
        case: _RedirectCase,
    ) -> None:
        app = web.Application(middlewares=[middleware])

        async def handler(request: web.Request) -> web.Response:
            raise case.raised

        app.router.add_get("/test", handler)
        client = await aiohttp_client(app)

        resp = await client.get("/test", allow_redirects=False)

        assert resp.status == case.expected_status
        assert resp.headers["Location"] == case.expected_location
        stats_monitor.report_metric.assert_any_call(
            INCREMENT, f"ai.backend.manager.api.status.{case.expected_status}"
        )
