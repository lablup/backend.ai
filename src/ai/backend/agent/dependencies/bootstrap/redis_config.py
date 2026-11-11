from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import NonMonitorableDependencyProvider


class RedisConfigDependency(NonMonitorableDependencyProvider[AgentUnifiedConfig, RedisConfig]):
    """Provides the redis configuration from the local config file."""

    @property
    @override
    def stage_name(self) -> str:
        return "redis-config (temp)"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: AgentUnifiedConfig) -> AsyncIterator[RedisConfig]:
        yield setup_input.redis
