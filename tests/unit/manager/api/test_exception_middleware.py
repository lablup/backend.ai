from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.common.metrics.http import build_api_metric_middleware
from ai.backend.manager.api.rest.app import api_middleware
from ai.backend.manager.api.rest.middleware import build_exception_middleware
from ai.backend.manager.errors.common import GenericForbidden, InternalServerError

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
