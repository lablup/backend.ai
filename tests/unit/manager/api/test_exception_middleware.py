from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from aiohttp import web
from aiohttp.typedefs import Middleware

from ai.backend.common.metrics.http import build_api_metric_middleware
from ai.backend.common.plugin.monitor import INCREMENT
from ai.backend.manager.api.rest.app import api_middleware
from ai.backend.manager.api.rest.middleware.exception import build_exception_middleware
from ai.backend.manager.errors.common import (
    GenericBadRequest,
    GenericForbidden,
    InternalServerError,
)

_EXCEPTION_MIDDLEWARE_LOGGER = "ai.backend.manager.api.rest.middleware.exception"


class _RecordingMetric:
    def __init__(self) -> None:
        self.observations: list[dict[str, Any]] = []

    def observe_request(self, **kwargs: Any) -> None:
        self.observations.append(kwargs)


def _build_app(metric: _RecordingMetric) -> web.Application:
    config_provider = MagicMock()
    config_provider.config.debug.enabled = False
    app = web.Application(
        middlewares=[
            build_exception_middleware(
                error_monitor=AsyncMock(),
                stats_monitor=AsyncMock(),
                config_provider=config_provider,
            ),
            build_api_metric_middleware(metric),
            api_middleware,
        ]
    )

    async def forbidden(request: web.Request) -> web.Response:
        raise GenericForbidden

    async def broken(request: web.Request) -> web.Response:
        raise InternalServerError

    app.router.add_route("GET", "/forbidden", forbidden)
    app.router.add_route("GET", "/broken", broken)
    return app


async def test_unmatched_route_is_logged_at_debug_and_counted(
    aiohttp_client: Any, caplog: pytest.LogCaptureFixture
) -> None:
    metric = _RecordingMetric()
    client = await aiohttp_client(_build_app(metric))

    with caplog.at_level(logging.DEBUG, logger=_EXCEPTION_MIDDLEWARE_LOGGER):
        resp = await client.get("/license")

    assert resp.status == 404
    assert [r.levelno for r in caplog.records] == [logging.DEBUG]
    assert metric.observations == [
        {
            "method": "GET",
            "endpoint": "/license",
            "error_code": metric.observations[0]["error_code"],
            "status_code": 404,
            "duration": metric.observations[0]["duration"],
        }
    ]


async def test_registered_handler_4xx_keeps_warning(
    aiohttp_client: Any, caplog: pytest.LogCaptureFixture
) -> None:
    metric = _RecordingMetric()
    client = await aiohttp_client(_build_app(metric))

    with caplog.at_level(logging.DEBUG, logger=_EXCEPTION_MIDDLEWARE_LOGGER):
        resp = await client.get("/forbidden")

    assert resp.status == 403
    assert [r.levelno for r in caplog.records] == [logging.WARNING]
    assert metric.observations[0]["status_code"] == 403


async def test_registered_handler_5xx_keeps_traceback(
    aiohttp_client: Any, caplog: pytest.LogCaptureFixture
) -> None:
    metric = _RecordingMetric()
    client = await aiohttp_client(_build_app(metric))

    with caplog.at_level(logging.DEBUG, logger=_EXCEPTION_MIDDLEWARE_LOGGER):
        resp = await client.get("/broken")

    assert resp.status == 500
    assert [r.levelno for r in caplog.records] == [logging.ERROR]
    assert caplog.records[0].exc_info is not None
    assert metric.observations[0]["status_code"] == 500


@dataclass(frozen=True)
class _ErrorCase:
    raised: web.HTTPException
    expected_status: int
    expected_error_type: str


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
            _ErrorCase(
                raised=web.HTTPNotFound(),
                expected_status=404,
                expected_error_type="https://api.backend.ai/probs/url-not-found",
            ),
            _ErrorCase(
                raised=web.HTTPForbidden(),
                expected_status=400,
                expected_error_type="https://api.backend.ai/probs/generic-bad-request",
            ),
            _ErrorCase(
                raised=GenericBadRequest("nope"),
                expected_status=400,
                expected_error_type="https://api.backend.ai/probs/generic-bad-request",
            ),
        ],
        ids=lambda case: type(case.raised).__name__,
    )
    async def test_error_is_rendered_as_problem_json(
        self,
        aiohttp_client: Any,
        middleware: Middleware,
        case: _ErrorCase,
    ) -> None:
        app = web.Application(middlewares=[middleware])

        async def handler(request: web.Request) -> web.Response:
            raise case.raised

        app.router.add_get("/test", handler)
        client = await aiohttp_client(app)

        resp = await client.get("/test")

        assert resp.status == case.expected_status
        assert (await resp.json())["type"] == case.expected_error_type

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

    async def test_unsupported_api_version_is_counted_as_failure(
        self,
        aiohttp_client: Any,
        middleware: Middleware,
        stats_monitor: AsyncMock,
    ) -> None:
        app = web.Application(middlewares=[middleware, api_middleware])

        async def handler(request: web.Request) -> web.Response:
            return web.Response(text="unreachable")

        app.router.add_get("/test", handler)
        client = await aiohttp_client(app)

        resp = await client.get("/test", headers={"X-BackendAI-Version": "v2.20170315"})

        assert resp.status == 400
        assert "Unsupported" in (await resp.json())["msg"]
        assert call(INCREMENT, "ai.backend.manager.api.failures") in (
            stats_monitor.report_metric.call_args_list
        )
