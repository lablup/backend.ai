from __future__ import annotations

import logging
import uuid
from typing import Any

import pytest
from aiohttp import web

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.middlewares.request_id import REQUEST_ID_HEADER, request_id_middleware
from ai.backend.logging.structured import StructuredLogger

LOGGER_NAME = "tests.common.request_id_middleware"


async def test_request_id_middleware_with_custom_request_id(aiohttp_client: Any) -> None:
    async def test_handler(request: web.Request) -> web.Response:
        assert current_request_id() == request.headers.get(REQUEST_ID_HEADER)
        return web.Response(text="ok")

    app = web.Application()
    app.middlewares.append(request_id_middleware)
    app.router.add_get("/", test_handler)

    client = await aiohttp_client(app)

    # Test with custom request ID
    test_id = str(uuid.uuid4())
    resp = await client.get("/", headers={REQUEST_ID_HEADER: test_id})
    assert resp.status == 200


async def test_request_id_middleware_without_request_id(aiohttp_client: Any) -> None:
    async def test_handler(request: web.Request) -> web.Response:
        assert current_request_id() is not None
        return web.Response(text="ok")

    app = web.Application()
    app.middlewares.append(request_id_middleware)
    app.router.add_get("/", test_handler)

    client = await aiohttp_client(app)

    # Test without request ID (should be None)
    resp = await client.get("/")
    assert resp.status == 200


async def test_generated_request_id_is_the_log_field(
    aiohttp_client: Any, caplog: pytest.LogCaptureFixture
) -> None:
    log = StructuredLogger(logging.getLogger(LOGGER_NAME))
    seen: list[str | None] = []

    async def test_handler(request: web.Request) -> web.Response:
        seen.append(current_request_id())
        log.info("handled")
        return web.Response(text="ok")

    app = web.Application()
    app.middlewares.append(request_id_middleware)
    app.router.add_get("/", test_handler)
    client = await aiohttp_client(app)

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        resp = await client.get("/")

    assert resp.status == 200
    (record,) = [r for r in caplog.records if r.name == LOGGER_NAME]
    assert seen[0] is not None
    assert record.__dict__["log_tag_request_id"] == seen[0]
