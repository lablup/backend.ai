from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.logging.types import LogLevel
from ai.backend.manager.config.provider import ManagerConfigProvider

from ..config import ConfigProviderDependency, ConfigProviderInput
from .config import BootstrapConfigDependency, BootstrapConfigInput
from .etcd import EtcdDependency


@dataclass
class BootstrapInput:
    """Input required for bootstrap stage.

    Contains the essential parameters: config file path and log level.
    """

    config_path: Path
    log_level: LogLevel = LogLevel.NOTSET


@dataclass
class BootstrapResources:
    """Container for bootstrap stage resources.

    Holds etcd and config provider initialized from bootstrap configuration.
    """

    etcd: AsyncEtcd
    config_provider: ManagerConfigProvider


class BootstrapComposer(DependencyComposer[BootstrapInput, BootstrapResources]):
    """Composes bootstrap dependencies.

    Composes the three-stage bootstrap initialization:
    1. Bootstrap config: Load bootstrap configuration from file
    2. Etcd: Initialize etcd with bootstrap config
    3. Config provider: Create config provider with etcd
    """

    @property
    def stage_name(self) -> str:
        return "bootstrap"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: BootstrapInput,
    ) -> AsyncIterator[BootstrapResources]:
        """Compose bootstrap dependencies in order.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Bootstrap input containing config path and log level

        Yields:
            BootstrapResources containing etcd and config provider
        """
        # Stage 1: Load bootstrap config
        bootstrap_config_dep = BootstrapConfigDependency()
        bootstrap_config_input = BootstrapConfigInput(
            config_path=setup_input.config_path,
            log_level=setup_input.log_level,
        )
        bootstrap_config = await stack.enter_dependency(
            bootstrap_config_dep,
            bootstrap_config_input,
        )

        # Stage 2: Initialize etcd
        etcd_dep = EtcdDependency()
        etcd = await stack.enter_dependency(
            etcd_dep,
            bootstrap_config,
        )

        # Stage 3: Create config provider
        config_dep = ConfigProviderDependency()
        config_provider_input = ConfigProviderInput(
            etcd=etcd,
            config_path=setup_input.config_path,
            log_level=setup_input.log_level,
        )
        config_provider = await stack.enter_dependency(
            config_dep,
            config_provider_input,
        )

        # Yield bootstrap resources
        yield BootstrapResources(
            etcd=etcd,
            config_provider=config_provider,
        )
