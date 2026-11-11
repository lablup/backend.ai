from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.types import safe_print_redis_config
from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig

log = StructuredLogger(logging.getLogger(__spec__.name))


class RedisConfigProvider(NonMonitorableDependencyProvider[StorageProxyUnifiedConfig, RedisConfig]):
    """Provider for the Redis configuration from the local config file."""

    @property
    @override
    def stage_name(self) -> str:
        return "redis-config"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: StorageProxyUnifiedConfig) -> AsyncIterator[RedisConfig]:
        log.info("redis config applied", redis_config=safe_print_redis_config(setup_input.redis))
        yield setup_input.redis
