from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.stage.types import Provisioner
from ai.backend.logging import LogLevel
from ai.backend.manager.config.loader.config_overrider import ConfigOverrider
from ai.backend.manager.config.loader.etcd_loader import (
    EtcdCommonConfigLoader,
    EtcdManagerConfigLoader,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import (
    LegacyEtcdLoader,
    LegacyEtcdVolumesLoader,
)
from ai.backend.manager.config.loader.loader_chain import LoaderChain
from ai.backend.manager.config.loader.toml_loader import TomlConfigLoader
from ai.backend.manager.config.loader.types import AbstractConfigLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.watchers.etcd import EtcdConfigWatcher


@dataclass
class ConfigProviderSpec:
    etcd: AsyncEtcd
    log_level: LogLevel
    config_path: Optional[Path] = None
    extra_config: Optional[Mapping[str, Any]] = None
    debug: bool = False


class ConfigProviderProvisioner(Provisioner[ConfigProviderSpec, ManagerConfigProvider]):
    @property
    def name(self) -> str:
        return "config_provider"

    async def setup(self, spec: ConfigProviderSpec) -> ManagerConfigProvider:
        # Create the chain of config loaders in the same order as the original implementation
        config_loaders: list[AbstractConfigLoader] = []

        # 1. TOML config loader (if config file is provided)
        if spec.config_path is not None:
            config_loaders.append(TomlConfigLoader(spec.config_path, "manager"))

        # 2. Legacy etcd loaders
        legacy_etcd_loader = LegacyEtcdLoader(spec.etcd)
        config_loaders.append(legacy_etcd_loader)
        config_loaders.append(LegacyEtcdVolumesLoader(spec.etcd))

        # 3. Current etcd loaders
        config_loaders.append(EtcdCommonConfigLoader(spec.etcd))
        config_loaders.append(EtcdManagerConfigLoader(spec.etcd))

        # 4. Config overrider (for command-line arguments)
        overrides: list[tuple[tuple[str, ...], Any]] = []
        if spec.debug:
            overrides.append((("debug", "enabled"), spec.debug))
        if spec.log_level and spec.log_level != LogLevel.NOTSET:
            overrides.extend([
                (("logging", "level"), spec.log_level),
                (("logging", "pkg-ns", "ai.backend"), spec.log_level),
                (("logging", "pkg-ns", "aiohttp"), spec.log_level),
            ])
        if spec.extra_config:
            # Convert extra_config dict to the required format
            def dict_to_tuples(
                d: Mapping[str, Any], prefix: tuple[str, ...] = ()
            ) -> list[tuple[tuple[str, ...], Any]]:
                result = []
                for k, v in d.items():
                    if isinstance(v, dict):
                        result.extend(dict_to_tuples(v, prefix + (k,)))
                    else:
                        result.append((prefix + (k,), v))
                return result

            overrides.extend(dict_to_tuples(spec.extra_config))
        if overrides:
            config_loaders.append(ConfigOverrider(overrides))

        # Create the unified config loader
        unified_config_loader = LoaderChain(config_loaders)

        # Create etcd config watcher for dynamic updates
        etcd_watcher = EtcdConfigWatcher(spec.etcd)

        # Create and return the config provider
        config_provider = await ManagerConfigProvider.create(
            unified_config_loader,
            etcd_watcher,
            legacy_etcd_loader,
        )

        return config_provider

    async def teardown(self, resource: ManagerConfigProvider) -> None:
        await resource.terminate()
