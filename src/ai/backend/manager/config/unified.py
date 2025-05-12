import asyncio
from typing import Awaitable, Callable, Optional

from ai.backend.manager.config.watchers.etcd import EtcdConfigWatcher

from .loader.legacy_etcd_loader import LegacyEtcdLoader
from .local import ManagerLocalConfig
from .shared import ManagerSharedConfig

SharedConfigChangeCallback = Callable[[ManagerSharedConfig], Awaitable[None]]


class ManagerUnifiedConfig:
    local: ManagerLocalConfig
    shared: ManagerSharedConfig
    legacy_etcd_config_loader: LegacyEtcdLoader
    etcd_watcher: EtcdConfigWatcher

    _etcd_watcher_task: Optional[asyncio.Task[None]]

    def __init__(
        self,
        local: ManagerLocalConfig,
        shared: ManagerSharedConfig,
        legacy_etcd_config_loader: LegacyEtcdLoader,
        etcd_watcher: EtcdConfigWatcher,
    ) -> None:
        self.local = local
        self.shared = shared
        self.legacy_etcd_config_loader = legacy_etcd_config_loader
        self.etcd_watcher = etcd_watcher

    async def _run_watcher(self) -> None:
        async for event in self.etcd_watcher.watch():
            # TODO: Handle all etcd_loader.load() here
            pass

    def start(self) -> None:
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
