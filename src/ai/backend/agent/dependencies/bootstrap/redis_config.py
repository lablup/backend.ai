from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common import config as common_config
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd


@dataclass(frozen=True)
class RedisConfigInput:
    """Input for the redis config stage.

    ``local_redis_config`` is the ``[redis]`` section of the local config, if present.
    """

    etcd: AsyncEtcd
    local_redis_config: RedisConfig | None = None


class RedisConfigDependency(NonMonitorableDependencyProvider[RedisConfigInput, RedisConfig]):
    """Provides the redis configuration.

    A ``[redis]`` section in the local config takes precedence; otherwise it is read from etcd,
    as server.py's read_agent_config() does.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "redis-config (temp)"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: RedisConfigInput) -> AsyncIterator[RedisConfig]:
        """Provide the redis config from the local config if set, else from etcd.

        Args:
            setup_input: Etcd client and the optional local redis config

        Yields:
            RedisConfig from the local config if present, otherwise loaded from etcd
        """
        if setup_input.local_redis_config is not None:
            yield setup_input.local_redis_config
            return

        _redis_config = common_config.redis_config_iv.check(
            await setup_input.etcd.get_prefix("config/redis"),
        )

        # Convert HostPortPair to dict format for compatibility
        redis_config_dict = _redis_config.copy()
        if isinstance(_redis_config.get("addr"), object):
            addr = _redis_config["addr"]
            if addr is not None:
                redis_config_dict["addr"] = f"{addr.host}:{addr.port}"

        redis_config = RedisConfig.model_validate(redis_config_dict)

        yield redis_config
