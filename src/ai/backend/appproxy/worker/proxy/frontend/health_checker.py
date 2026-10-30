from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import override

from ai.backend.common.health_checker.abc import ServiceHealthChecker
from ai.backend.common.health_checker.types import (
    ComponentHealthStatus,
    ComponentId,
    ServiceGroup,
    ServiceHealth,
)

PROXY_FRONTEND: ServiceGroup = ServiceGroup("proxy-frontend")

_SERVING_COMPONENT_ID: ComponentId = ComponentId("serving")
_DEFAULT_TIMEOUT = 1.0


class ProxyFrontendServingHealthChecker(ServiceHealthChecker):
    """Unhealthy until the proxy frontend opens its ports after the initial circuit load."""

    _serving: asyncio.Event
    _timeout: float

    def __init__(self, serving: asyncio.Event, *, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._serving = serving
        self._timeout = timeout

    @property
    @override
    def target_service_group(self) -> ServiceGroup:
        return PROXY_FRONTEND

    @property
    @override
    def timeout(self) -> float:
        return self._timeout

    @override
    async def check_service(self) -> ServiceHealth:
        is_serving = self._serving.is_set()
        return ServiceHealth(
            results={
                _SERVING_COMPONENT_ID: ComponentHealthStatus(
                    is_healthy=is_serving,
                    last_checked_at=datetime.now(UTC),
                    error_message=None if is_serving else "the initial circuit load is not done",
                ),
            },
        )
