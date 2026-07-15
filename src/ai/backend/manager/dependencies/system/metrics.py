from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.metrics.metric import CommonMetricRegistry

from .base import SystemDependency


class MetricsDependency(SystemDependency[CommonMetricRegistry]):
    """Provides CommonMetricRegistry singleton."""

    @property
    @override
    def stage_name(self) -> str:
        return "metrics"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: object) -> AsyncIterator[CommonMetricRegistry]:
        yield CommonMetricRegistry.instance()
