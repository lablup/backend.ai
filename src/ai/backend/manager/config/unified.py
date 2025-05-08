import asyncio
from collections.abc import Mapping
from typing import Any, Awaitable, Callable, Optional

from .loader.etcd_loader import LegacyEtcdLoader
from .loader.types import AbstractConfigLoader
from .local import ManagerLocalConfig
from .shared import ManagerSharedConfig
from .watchers.etcd_watcher import EtcdConfigWatcher

SharedConfigChangeCallback = Callable[[ManagerSharedConfig], Awaitable[None]]


class ManagerUnifiedConfig:
    local: ManagerLocalConfig
    shared: ManagerSharedConfig

    local_config_loader: AbstractConfigLoader
    shared_config_loader: LegacyEtcdLoader

    _shared_config_watcher: EtcdConfigWatcher
    _shared_config_watcher_task: asyncio.Task[Any]
    _shared_config_change_callback: Optional[SharedConfigChangeCallback]

    def __init__(
        self,
        local: ManagerLocalConfig,
        shared: ManagerSharedConfig,
        local_config_loader: AbstractConfigLoader,
        shared_config_loader: LegacyEtcdLoader,
        shared_config_change_callback: Optional[SharedConfigChangeCallback] = None,
    ) -> None:
        self.local = local
        self.shared = shared
        self.local_config_loader = local_config_loader
        self.shared_config_loader = shared_config_loader
        self._shared_config_watcher = EtcdConfigWatcher(shared_config_loader)
        self._shared_config_change_callback = shared_config_change_callback

    def start_watcher(self) -> None:
        self._shared_config_watcher_task = asyncio.create_task(
            self._watch_shared_config_change(), name="shared_cfg_watcher"
        )

    def stop_watcher(self) -> None:
        self._shared_config_watcher_task.cancel()

    def register_shared_config_change_callback(self, cb: SharedConfigChangeCallback) -> None:
        self._shared_config_change_callback = cb

    async def _load_local_cfg(self, raw_cfg: Mapping[str, Any]) -> ManagerLocalConfig:
        return ManagerLocalConfig(**raw_cfg)

    async def _load_shared_cfg(self, raw_cfg: Mapping[str, Any]) -> ManagerSharedConfig:
        shared_cfg = ManagerSharedConfig(**raw_cfg)
        if self._shared_config_change_callback:
            await self._shared_config_change_callback(self.shared)
        return shared_cfg

    async def _watch_shared_config_change(self) -> None:
        async for raw_local in self._shared_config_watcher.watch():
            await self._load_shared_cfg(raw_local)

    async def load_shared_config(self) -> None:
        shared_cfg_loader = LegacyEtcdLoader(self.local.etcd.to_dataclass())
        raw_shared_cfg = await shared_cfg_loader.load()
        shared_cfg = ManagerSharedConfig.model_validate(raw_shared_cfg)
        self.shared = shared_cfg
        self.shared_config_loader = shared_cfg_loader
        shared_config_watcher = EtcdConfigWatcher(shared_cfg_loader)
        self._shared_config_watcher = shared_config_watcher
