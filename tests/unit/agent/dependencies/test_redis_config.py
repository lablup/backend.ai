from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from ai.backend.agent.dependencies.bootstrap.redis_config import RedisConfigDependency
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes


class TestRedisConfigDependency:
    @pytest.fixture
    async def etcd_with_redis_config(self, etcd: AsyncEtcd) -> AsyncIterator[AsyncEtcd]:
        """Etcd fixture with redis config set up."""
        await etcd.put_prefix(
            "config/redis",
            {
                "addr": {"host": "127.0.0.1", "port": "6379"},
            },
            scope=ConfigScopes.GLOBAL,
        )
        yield etcd

    @pytest.mark.asyncio
    async def test_redis_config_reads_from_etcd(self, etcd_with_redis_config: AsyncEtcd) -> None:
        """Test that redis config is read from etcd successfully."""
        dependency = RedisConfigDependency()

        async with dependency.provide(etcd_with_redis_config) as redis_config:
            assert redis_config is not None
            assert redis_config.addr is not None

    @pytest.mark.asyncio
    async def test_redis_config_converts_host_port_pair(self, etcd: AsyncEtcd) -> None:
        """Test that HostPortPair is converted to string format."""
        # Set up redis config in etcd with HostPortPair format
        await etcd.put_prefix(
            "config/redis",
            {
                "addr": {"host": "192.168.1.100", "port": "6380"},
                "password": "test-password",
            },
            scope=ConfigScopes.GLOBAL,
        )

        dependency = RedisConfigDependency()

        async with dependency.provide(etcd) as redis_config:
            # Should be converted to "host:port" format
            assert redis_config.addr is not None
            if isinstance(redis_config.addr, str):
                assert ":" in redis_config.addr
                assert redis_config.addr == "192.168.1.100:6380"
            assert redis_config.password == "test-password"
