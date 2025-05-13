import asyncio
import logging
from typing import Awaitable, Callable, Optional

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.loader.loader_chain import LoaderChain
from ai.backend.manager.config.watchers.etcd import EtcdConfigWatcher

from .loader.legacy_etcd_loader import LegacyEtcdLoader
from .shared import ManagerUnifiedConfig

SharedConfigChangeCallback = Callable[[ManagerUnifiedConfig], Awaitable[None]]

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ManagerConfigProvider:
    _loader: LoaderChain
    _config: Optional[ManagerUnifiedConfig]
    _etcd_watcher: EtcdConfigWatcher
    _etcd_watcher_task: Optional[asyncio.Task[None]]
    # TODO: Remove `_legacy_etcd_config_loader` when legacy etcd methods are removed
    _legacy_etcd_config_loader: LegacyEtcdLoader

    def __init__(
        self,
        loader: LoaderChain,
        etcd_watcher: EtcdConfigWatcher,
        legacy_etcd_config_loader: LegacyEtcdLoader,
    ) -> None:
        self._loader = loader
        self._config = None
        self._etcd_watcher = etcd_watcher
        self._etcd_watcher_task = None
        self._legacy_etcd_config_loader = legacy_etcd_config_loader

    @property
    def config(self) -> ManagerUnifiedConfig:
        if self._config is None:
            raise RuntimeError("Shared config is not initialized")
        return self._config

    @property
    def legacy_etcd_config_loader(self) -> LegacyEtcdLoader:
        return self._legacy_etcd_config_loader

    async def _run_watcher(self) -> None:
        async for event in self._etcd_watcher.watch():
            raw_config = await self._loader.load()
            self._config = ManagerUnifiedConfig.model_validate(raw_config)
            log.debug("config reloaded due to etcd event.")

    async def init(self) -> None:
        raw_config = await self._loader.load()
        self._config = ManagerUnifiedConfig.model_validate(raw_config)
        self._etcd_watcher_task = asyncio.create_task(self._run_watcher())

    async def terminate(self) -> None:
        if self._etcd_watcher_task:
            self._etcd_watcher_task.cancel()
            try:
                await self._etcd_watcher_task
            except asyncio.CancelledError:
                pass
            finally:
                self._etcd_watcher_task = None
