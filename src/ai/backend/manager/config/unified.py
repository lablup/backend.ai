import asyncio
from typing import Awaitable, Callable, Optional

from ai.backend.manager.config.loader.loader_chain import LoaderChain
from ai.backend.manager.config.watchers.etcd import EtcdConfigWatcher

from .loader.legacy_etcd_loader import LegacyEtcdLoader
from .shared import ManagerSharedConfig

SharedConfigChangeCallback = Callable[[ManagerSharedConfig], Awaitable[None]]


class ManagerUnifiedConfig:
    _config: ManagerSharedConfig
    _loader: LoaderChain
    _etcd_watcher: EtcdConfigWatcher
    _etcd_watcher_task: Optional[asyncio.Task[None]]
    _legacy_etcd_config_loader: LegacyEtcdLoader

    def __init__(
        self,
        loader: LoaderChain,
        legacy_etcd_config_loader: LegacyEtcdLoader,
        etcd_watcher: EtcdConfigWatcher,
    ) -> None:
        self._loader = loader
        self._legacy_etcd_config_loader = legacy_etcd_config_loader
        self._etcd_watcher = etcd_watcher

    @property
    def shared(self) -> ManagerSharedConfig:
        return self._config

    @property
    def legacy_etcd_config_loader(self) -> LegacyEtcdLoader:
        return self._legacy_etcd_config_loader

    async def _run_watcher(self) -> None:
        async for event in self._etcd_watcher.watch():
            # TODO: Handle all etcd_loader.load() here
            pass

    async def load(self) -> None:
        raw_shared_config = await self._loader.load()
        self._config = ManagerSharedConfig.model_validate(raw_shared_config)
        self._etcd_watcher_task = asyncio.create_task(self._run_watcher())

    async def stop(self) -> None:
        if self._etcd_watcher_task:
            self._etcd_watcher_task.cancel()
            try:
                await self._etcd_watcher_task
            except asyncio.CancelledError:
                pass
            finally:
                self._etcd_watcher_task = None
