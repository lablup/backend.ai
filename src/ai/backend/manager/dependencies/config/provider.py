from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.logging.types import LogLevel
from ai.backend.manager.config.loader.config_overrider import ConfigOverrider
from ai.backend.manager.config.loader.etcd_loader import (
    EtcdCommonConfigLoader,
    EtcdManagerConfigLoader,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.loader.loader_chain import LoaderChain
from ai.backend.manager.config.loader.toml_loader import TomlConfigLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.watchers.etcd import EtcdConfigWatcher


@dataclass
class ConfigProviderInput:
    """Input required for config provider setup.

    Contains etcd client and configuration parameters.
    """

    etcd: AsyncEtcd
    config_path: Path
    log_level: LogLevel = LogLevel.NOTSET


class ConfigProviderDependency(
    NonMonitorableDependencyProvider[ConfigProviderInput, ManagerConfigProvider]
):
    """Provides ManagerConfigProvider lifecycle management.

    Creates the config provider with file, env, etcd-based loaders and watchers.
    """

    @property
    def stage_name(self) -> str:
        return "config-provider"

    @asynccontextmanager
    async def provide(
        self, setup_input: ConfigProviderInput
    ) -> AsyncIterator[ManagerConfigProvider]:
        """Initialize and provide a config provider.

        Args:
            setup_input: Input containing etcd client and config parameters

        Yields:
            Initialized ManagerConfigProvider
        """
        # Create loader chain following server.py pattern
        loaders: list = []

        # Add file loader if config path is provided
        if setup_input.config_path:
            toml_loader = TomlConfigLoader(setup_input.config_path, "manager")
            loaders.append(toml_loader)

        # Add legacy etcd loader
        legacy_etcd_loader = LegacyEtcdLoader(setup_input.etcd)
        loaders.append(legacy_etcd_loader)

        # Add etcd config loaders
        loaders.append(EtcdCommonConfigLoader(setup_input.etcd))
        loaders.append(EtcdManagerConfigLoader(setup_input.etcd))

        # Add overrides
        overrides: list[tuple[tuple[str, ...], Any]] = [
            (("debug", "enabled"), setup_input.log_level == LogLevel.DEBUG),
        ]
        if setup_input.log_level != LogLevel.NOTSET:
            overrides += [
                (("logging", "level"), setup_input.log_level),
                (("logging", "pkg-ns", "ai.backend"), setup_input.log_level),
            ]
        loaders.append(ConfigOverrider(overrides))

        # Create unified loader chain
        unified_loader = LoaderChain(loaders)
        etcd_watcher = EtcdConfigWatcher(setup_input.etcd)

        # Create the config provider
        config_provider = await ManagerConfigProvider.create(
            unified_loader,
            etcd_watcher,
            legacy_etcd_loader,
        )

        try:
            yield config_provider
        finally:
            await config_provider.terminate()
