import asyncio
import logging
from typing import Awaitable, Callable, Self

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.loader.loader_chain import LoaderChain
from ai.backend.manager.config.watchers.etcd import EtcdConfigWatcher

from .loader.legacy_etcd_loader import LegacyEtcdLoader
from .unified import ManagerUnifiedConfig

SharedConfigChangeCallback = Callable[[ManagerUnifiedConfig], Awaitable[None]]

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ManagerConfigProvider:
    _loader: LoaderChain
    _config: ManagerUnifiedConfig
    _etcd_watcher: EtcdConfigWatcher
    _etcd_watcher_task: asyncio.Task[None]
    # TODO: Remove `_legacy_etcd_config_loader` when legacy etcd methods are removed
    _legacy_etcd_config_loader: LegacyEtcdLoader

    def __init__(
        self,
        loader: LoaderChain,
        config: ManagerUnifiedConfig,
        etcd_watcher: EtcdConfigWatcher,
        legacy_etcd_config_loader: LegacyEtcdLoader,
    ) -> None:
        self._loader = loader
        self._config = config
        self._etcd_watcher = etcd_watcher
        self._legacy_etcd_config_loader = legacy_etcd_config_loader
        self._etcd_watcher_task = asyncio.create_task(self._run_watcher())

    @classmethod
    async def create(
        cls,
        loader: LoaderChain,
        etcd_watcher: EtcdConfigWatcher,
        legacy_etcd_config_loader: LegacyEtcdLoader,
    ) -> Self:
        raw_config = await loader.load()
        config = ManagerUnifiedConfig.model_validate(raw_config, by_name=True)
        return cls(loader, config, etcd_watcher, legacy_etcd_config_loader)

    @property
    def config(self) -> ManagerUnifiedConfig:
        return self._config

    def reload(self, config: ManagerUnifiedConfig) -> None:
        self._config = config

    @property
    def legacy_etcd_config_loader(self) -> LegacyEtcdLoader:
        return self._legacy_etcd_config_loader

    async def _run_watcher(self) -> None:
        async for event in self._etcd_watcher.watch():
            raw_config = await self._loader.load()
            self._config = ManagerUnifiedConfig.model_validate(raw_config, by_name=True)
            log.debug("config reloaded due to etcd event.")

    async def terminate(self) -> None:
        if self._etcd_watcher_task:
            self._etcd_watcher_task.cancel()
            try:
                await self._etcd_watcher_task
            except asyncio.CancelledError:
                pass
