from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common import config as common_config
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd


class RedisConfigDependency(NonMonitorableDependencyProvider[AsyncEtcd, RedisConfig]):
    """Reads redis configuration from etcd.

    Matches the behavior in server.py's read_agent_config() (lines 457-473).
    """

    @property
    def stage_name(self) -> str:
        return "redis-config (temp)"

    @asynccontextmanager
    async def provide(self, setup_input: AsyncEtcd) -> AsyncIterator[RedisConfig]:
        """Read redis config from etcd.

        Args:
            setup_input: Etcd client

        Yields:
            RedisConfig loaded from etcd
        """
        # Read redis config from etcd (same as server.py read_agent_config() lines 459-473)
        _redis_config = common_config.redis_config_iv.check(
            await setup_input.get_prefix("config/redis"),
        )

        # Convert HostPortPair to dict format for compatibility
        redis_config_dict = _redis_config.copy()
        if isinstance(_redis_config.get("addr"), object):
            addr = _redis_config["addr"]
            if addr is not None:
                redis_config_dict["addr"] = f"{addr.host}:{addr.port}"

        redis_config = RedisConfig.model_validate(redis_config_dict)

        yield redis_config
