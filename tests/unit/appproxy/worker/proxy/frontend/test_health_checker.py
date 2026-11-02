from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from ai.backend.appproxy.worker.proxy.frontend.health_checker import (
    ProxyFrontendServingHealthChecker,
)


@dataclass(frozen=True)
class _ServingCase:
    name: str
    serving: bool
    expected_healthy: bool


@pytest.fixture
def serving_health_checker(case: _ServingCase) -> ProxyFrontendServingHealthChecker:
    serving = asyncio.Event()
    if case.serving:
        serving.set()
    return ProxyFrontendServingHealthChecker(serving)


class TestProxyFrontendServingHealthChecker:
    @pytest.mark.parametrize(
        "case",
        [
            _ServingCase(name="before-the-initial-load", serving=False, expected_healthy=False),
            _ServingCase(name="serving", serving=True, expected_healthy=True),
        ],
        ids=lambda case: case.name,
    )
    async def test_reports_healthy_only_while_the_frontend_serves(
        self, case: _ServingCase, serving_health_checker: ProxyFrontendServingHealthChecker
    ) -> None:
        service_health = await serving_health_checker.check_service()
        assert [status.is_healthy for status in service_health.results.values()] == [
            case.expected_healthy
        ]
