from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from prometheus_client import CollectorRegistry, Counter, Histogram

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
    InvalidAPIParameters,
)
from ai.backend.common.metrics.http import build_api_metric_middleware
from ai.backend.common.metrics.metric import APIMetricObserver
from ai.backend.common.middlewares.request_id import (
    OPERATION_HEADER,
    request_id_middleware,
)


class TestAPIMetricMiddlewareWithOperation:
    async def test_successful_request_with_operation_header(self, aiohttp_client: Any) -> None:
        mock_metric = MagicMock()

        async def test_handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        app = web.Application(
            middlewares=[
                request_id_middleware,
                build_api_metric_middleware(mock_metric),
            ]
        )
        app.router.add_get("/test", test_handler)

        client = await aiohttp_client(app)
        resp = await client.get("/test", headers={OPERATION_HEADER: "create_session"})
        assert resp.status == 200

        mock_metric.observe_request.assert_called_once()
        call_kwargs = mock_metric.observe_request.call_args.kwargs
        assert call_kwargs["client_operation"] == "create_session"
        assert call_kwargs["error_code"] is None

    async def test_successful_request_without_operation_header(self, aiohttp_client: Any) -> None:
        mock_metric = MagicMock()

        async def test_handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        app = web.Application(
            middlewares=[
                request_id_middleware,
                build_api_metric_middleware(mock_metric),
            ]
        )
        app.router.add_get("/test", test_handler)

        client = await aiohttp_client(app)
        resp = await client.get("/test")
        assert resp.status == 200

        mock_metric.observe_request.assert_called_once()
        call_kwargs = mock_metric.observe_request.call_args.kwargs
        assert call_kwargs["client_operation"] == ""
        assert call_kwargs["error_code"] is None

    async def test_failed_request_still_passes_client_operation_to_observer(
        self, aiohttp_client: Any
    ) -> None:
        mock_metric = MagicMock()

        async def test_handler(request: web.Request) -> web.Response:
            raise InvalidAPIParameters("test error")

        app = web.Application(
            middlewares=[
                request_id_middleware,
                build_api_metric_middleware(mock_metric),
            ]
        )
        app.router.add_get("/test", test_handler)

        client = await aiohttp_client(app)
        resp = await client.get("/test", headers={OPERATION_HEADER: "should_be_ignored"})
        assert resp.status == 400

        mock_metric.observe_request.assert_called_once()
        call_kwargs = mock_metric.observe_request.call_args.kwargs
        assert call_kwargs["error_code"] is not None
        assert call_kwargs["client_operation"] == "should_be_ignored"

    async def test_invalid_operation_header_is_sanitized(self, aiohttp_client: Any) -> None:
        mock_metric = MagicMock()

        async def test_handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        app = web.Application(
            middlewares=[
                request_id_middleware,
                build_api_metric_middleware(mock_metric),
            ]
        )
        app.router.add_get("/test", test_handler)

        client = await aiohttp_client(app)
        resp = await client.get(
            "/test", headers={OPERATION_HEADER: "invalid operation with spaces"}
        )
        assert resp.status == 200

        mock_metric.observe_request.assert_called_once()
        call_kwargs = mock_metric.observe_request.call_args.kwargs
        assert call_kwargs["client_operation"] == ""

    async def test_metric_middleware_without_request_id_middleware(
        self, aiohttp_client: Any
    ) -> None:
        mock_metric = MagicMock()

        async def test_handler(request: web.Request) -> web.Response:
            return web.Response(text="ok")

        app = web.Application(
            middlewares=[
                build_api_metric_middleware(mock_metric),
            ]
        )
        app.router.add_get("/test", test_handler)

        client = await aiohttp_client(app)
        resp = await client.get("/test")
        assert resp.status == 200

        mock_metric.observe_request.assert_called_once()
        call_kwargs = mock_metric.observe_request.call_args.kwargs
        assert call_kwargs["client_operation"] == ""


class TestAPIMetricObserverClientOperation:
    @pytest.fixture(autouse=True)
    def _isolate_prometheus_registry(self) -> None:
        """Use a fresh registry to avoid cross-test collisions."""
        registry = CollectorRegistry()
        self.observer = APIMetricObserver.__new__(APIMetricObserver)
        label_names = ["method", "endpoint", "domain", "operation", "error_detail", "status_code"]
        self.observer._request_count = Counter(
            name="test_api_request_count",
            documentation="test",
            labelnames=label_names,
            registry=registry,
        )
        self.observer._request_duration_sec = Histogram(
            name="test_api_request_duration_sec",
            documentation="test",
            labelnames=label_names,
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
            registry=registry,
        )

    def test_success_with_client_operation_populates_label(self) -> None:
        self.observer.observe_request(
            method="GET",
            endpoint="/test",
            error_code=None,
            status_code=200,
            duration=0.1,
            client_operation="list_sessions",
        )
        sample = self.observer._request_count.labels(
            method="GET",
            endpoint="/test",
            domain="",
            operation="list_sessions",
            error_detail="",
            status_code=200,
        )
        assert sample._value.get() == 1.0

    def test_success_without_client_operation_has_empty_label(self) -> None:
        self.observer.observe_request(
            method="GET",
            endpoint="/test",
            error_code=None,
            status_code=200,
            duration=0.1,
        )
        sample = self.observer._request_count.labels(
            method="GET",
            endpoint="/test",
            domain="",
            operation="",
            error_detail="",
            status_code=200,
        )
        assert sample._value.get() == 1.0

    def test_error_code_takes_precedence_over_client_operation(self) -> None:
        error_code = ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
        self.observer.observe_request(
            method="POST",
            endpoint="/test",
            error_code=error_code,
            status_code=400,
            duration=0.2,
            client_operation="should_be_ignored",
        )
        sample = self.observer._request_count.labels(
            method="POST",
            endpoint="/test",
            domain=ErrorDomain.API,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.BAD_REQUEST,
            status_code=400,
        )
        assert sample._value.get() == 1.0
