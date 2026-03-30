from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.logging.types import LogLevel

from .config import AgentConfigLoaderDependency, AgentConfigLoaderInput
from .etcd import AgentEtcdDependency
from .redis_config import RedisConfigDependency


@dataclass
class AgentBootstrapInput:
    """Input required for agent bootstrap stage.

    Contains the essential parameters: config file path and log level,
    matching server.py's main() function parameters.
    """

    config_path: Path | None = None
    log_level: LogLevel = LogLevel.NOTSET


@dataclass
class AgentBootstrapResources:
    """Container for agent bootstrap stage resources.

    Holds loaded config, initialized etcd client, and redis config from etcd.
    """

    config: AgentUnifiedConfig
    etcd: AsyncEtcd
    redis_config: RedisConfig


class AgentBootstrapComposer(DependencyComposer[AgentBootstrapInput, AgentBootstrapResources]):
    """Composes agent bootstrap dependencies.

    Composes the three-stage bootstrap initialization matching server.py:
    1. Config loader: Load and validate AgentUnifiedConfig (same as server.py main())
    2. Etcd: Initialize etcd client (same as server.py etcd_ctx())
    3. Redis config: Read redis config from etcd (same as server.py read_agent_config())
    """

    @property
    def stage_name(self) -> str:
        return "bootstrap"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: AgentBootstrapInput,
    ) -> AsyncIterator[AgentBootstrapResources]:
        """Compose bootstrap dependencies in order.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Bootstrap input containing config path and log level

        Yields:
            AgentBootstrapResources containing config and etcd
        """
        # Stage 1: Load config (same as server.py main() lines 1598-1646)
        config = await stack.enter_dependency(
            AgentConfigLoaderDependency(),
            AgentConfigLoaderInput(
                config_path=setup_input.config_path,
                log_level=setup_input.log_level,
            ),
        )

        # Stage 2: Initialize etcd (same as server.py etcd_ctx() lines 1345-1367)
        etcd = await stack.enter_dependency(
            AgentEtcdDependency(),
            config,
        )

        # Stage 3: Read redis config from etcd
        # (same as server.py read_agent_config() lines 457-473)
        redis_config = await stack.enter_dependency(
            RedisConfigDependency(),
            etcd,
        )

        # Yield bootstrap resources
        yield AgentBootstrapResources(
            config=config,
            etcd=etcd,
            redis_config=redis_config,
        )
