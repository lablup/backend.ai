from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.configs.loader.redis_loader import load_redis_config
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd


@dataclass(frozen=True)
class RedisConfigInput:
    etcd: AsyncEtcd
    local_redis: RedisConfig | None


class RedisConfigDependency(NonMonitorableDependencyProvider[RedisConfigInput, RedisConfig]):
    """Reads the redis configuration from etcd and the local config file, as server.py does."""

    @property
    @override
    def stage_name(self) -> str:
        return "redis-config (temp)"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: RedisConfigInput) -> AsyncIterator[RedisConfig]:
        yield await load_redis_config(setup_input.etcd, setup_input.local_redis)
