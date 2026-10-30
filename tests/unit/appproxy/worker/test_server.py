from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.appproxy.worker.server import proxy_frontend_serving_ctx


@pytest.fixture
def root_context_with_loaded_circuits() -> MagicMock:
    root_context = MagicMock()
    root_context.proxy_frontend = MagicMock(start=AsyncMock(), stop=AsyncMock())
    root_context.proxy_frontend_serving = asyncio.Event()
    root_context.health_probe = MagicMock(check_all=AsyncMock())
    return root_context


class TestProxyFrontendServingContext:
    async def test_entering_starts_the_frontend_and_refreshes_readiness(
        self, root_context_with_loaded_circuits: MagicMock
    ) -> None:
        root_context = root_context_with_loaded_circuits
        async with proxy_frontend_serving_ctx(root_context):
            root_context.proxy_frontend.start.assert_awaited_once()
            assert root_context.proxy_frontend_serving.is_set()
            root_context.health_probe.check_all.assert_awaited_once()

    async def test_leaving_stops_the_frontend_and_reports_not_serving(
        self, root_context_with_loaded_circuits: MagicMock
    ) -> None:
        root_context = root_context_with_loaded_circuits
        async with proxy_frontend_serving_ctx(root_context):
            pass
        root_context.proxy_frontend.stop.assert_awaited_once()
        assert not root_context.proxy_frontend_serving.is_set()
