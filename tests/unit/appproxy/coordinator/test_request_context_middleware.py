from __future__ import annotations

import logging

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.coordinator.server import request_context_aware_middleware
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.middlewares.request_id import REQUEST_ID_HEADER
from ai.backend.logging.structured import StructuredLogger

_LOGGER_NAME = "tests.appproxy.coordinator.request_context"


class TestRequestContextAwareMiddleware:
    @pytest.fixture
    def logger(self) -> StructuredLogger:
        return StructuredLogger(logging.getLogger(_LOGGER_NAME))

    async def _run(
        self, request: web.Request, logger: StructuredLogger
    ) -> tuple[str | None, web.StreamResponse]:
        seen: list[str | None] = []

        async def handler(_request: web.Request) -> web.StreamResponse:
            seen.append(current_request_id())
            logger.info("handled")
            return web.Response()

        response = await request_context_aware_middleware(request, handler)
        return seen[0], response

    async def test_header_request_id_is_the_scope_and_log_field(
        self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture
    ) -> None:
        request = make_mocked_request("GET", "/", headers={REQUEST_ID_HEADER: "worker-req-1"})

        with caplog.at_level(logging.INFO, logger=_LOGGER_NAME):
            seen_request_id, _ = await self._run(request, logger)

        assert seen_request_id == "worker-req-1"
        assert caplog.records[-1].__dict__["log_tag_request_id"] == "worker-req-1"
        assert request["request_id"] == "worker-req-1"

    async def test_generates_request_id_without_header(
        self, logger: StructuredLogger, caplog: pytest.LogCaptureFixture
    ) -> None:
        request = make_mocked_request("GET", "/")

        with caplog.at_level(logging.INFO, logger=_LOGGER_NAME):
            seen_request_id, _ = await self._run(request, logger)

        assert seen_request_id
        assert caplog.records[-1].__dict__["log_tag_request_id"] == seen_request_id
        assert request["request_id"] == seen_request_id

    async def test_scope_closes_after_the_request(self, logger: StructuredLogger) -> None:
        request = make_mocked_request("GET", "/", headers={REQUEST_ID_HEADER: "worker-req-2"})

        await self._run(request, logger)

        assert current_request_id() is None
