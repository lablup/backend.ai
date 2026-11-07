from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.configs.loader.redis_loader import load_redis_config
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import safe_print_redis_config
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class RedisConfigProviderInput:
    etcd: AsyncEtcd
    local_redis: RedisConfig | None


class RedisConfigProvider(NonMonitorableDependencyProvider[RedisConfigProviderInput, RedisConfig]):
    """Provider for the Redis configuration from etcd and the local config file."""

    @property
    @override
    def stage_name(self) -> str:
        return "redis-config"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: RedisConfigProviderInput) -> AsyncIterator[RedisConfig]:
        redis_config = await load_redis_config(setup_input.etcd, setup_input.local_redis)
        log.info("redis config applied", redis_config=safe_print_redis_config(redis_config))
        yield redis_config
