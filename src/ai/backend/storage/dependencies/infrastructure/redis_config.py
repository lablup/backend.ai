from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import safe_print_redis_config
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RedisConfigProvider(NonMonitorableDependencyProvider[AsyncEtcd, RedisConfig]):
    """Provider for the Redis configuration stored in etcd."""

    @property
    @override
    def stage_name(self) -> str:
        return "redis-config"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: AsyncEtcd) -> AsyncIterator[RedisConfig]:
        # TODO: Override UnifiedConfig with etcd values
        raw_redis_config = await setup_input.get_prefix("config/redis")
        redis_config = RedisConfig.model_validate(raw_redis_config)
        log.info("configured redis_config: {0}", safe_print_redis_config(redis_config))
        yield redis_config
