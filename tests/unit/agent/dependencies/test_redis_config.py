from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from ai.backend.agent.dependencies.bootstrap.redis_config import (
    RedisConfigDependency,
    RedisConfigInput,
)
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes


class TestRedisConfigDependency:
    @pytest.fixture
    async def etcd_with_redis_config(self, etcd: AsyncEtcd) -> AsyncIterator[AsyncEtcd]:
        await etcd.put_prefix(
            "config/redis",
            {
                "addr": {"host": "192.168.1.100", "port": "6380"},
                "password": "etcd-password",
            },
            scope=ConfigScopes.GLOBAL,
        )
        yield etcd

    async def test_reads_address_from_etcd(self, etcd_with_redis_config: AsyncEtcd) -> None:
        dependency = RedisConfigDependency()

        async with dependency.provide(
            RedisConfigInput(etcd=etcd_with_redis_config, local_redis=None)
        ) as redis_config:
            assert redis_config.addr is not None
            assert redis_config.addr.address == "192.168.1.100:6380"

    async def test_reads_password_only_from_local_config(
        self, etcd_with_redis_config: AsyncEtcd
    ) -> None:
        dependency = RedisConfigDependency()
        local_redis = RedisConfig.model_validate({"password": "local-password"})

        async with dependency.provide(
            RedisConfigInput(etcd=etcd_with_redis_config, local_redis=local_redis)
        ) as redis_config:
            assert redis_config.password == "local-password"

    async def test_ignores_password_in_etcd(self, etcd_with_redis_config: AsyncEtcd) -> None:
        dependency = RedisConfigDependency()

        async with dependency.provide(
            RedisConfigInput(etcd=etcd_with_redis_config, local_redis=None)
        ) as redis_config:
            assert redis_config.password is None
