import asyncio
import sys
from collections.abc import Mapping
from pathlib import Path
from pprint import pformat
from typing import Any, Awaitable, Callable, Optional, Self

from ai.backend.logging.types import LogLevel
from ai.backend.manager.config.loader.etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.loader.types import AbstractConfigLoader
from ai.backend.manager.config.shared import ManagerSharedConfig
from ai.backend.manager.config.watchers.etcd_watcher import EtcdConfigWatcher

from .local import ManagerLocalConfig

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
        shared_config_watcher: EtcdConfigWatcher,
        shared_config_change_callback: Optional[SharedConfigChangeCallback] = None,
    ) -> None:
        self.local = local
        self.shared = shared
        self.local_config_loader = local_config_loader
        self.shared_config_loader = shared_config_loader
        self._shared_config_watcher = shared_config_watcher
        self._shared_config_change_callback = shared_config_change_callback

    async def start_watcher(self) -> None:
        # Initial load
        self._shared_config_watcher_task = asyncio.create_task(
            self._watch_shared_config_change(), name="shared_cfg_watcher"
        )

    async def stop_watcher(self) -> None:
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

    @classmethod
    async def load(
        cls, config_path: Optional[Path] = None, log_level: LogLevel = LogLevel.NOTSET
    ) -> Self:
        local_cfg, local_cfg_loader = await ManagerLocalConfig.load(config_path, log_level)

        if local_cfg.debug.enabled:
            print("== Manager configuration ==", file=sys.stderr)
            print(pformat(local_cfg), file=sys.stderr)

        # etcd_config는 local_config가 먼저 로드된 후에야 로드될 수 있음.
        # 그래서 unified_config load 시점에 두 개를 한 꺼번에 로드하는건 부적절함.
        shared_cfg_loader = LegacyEtcdLoader(local_cfg.etcd)
        raw_shared_cfg = await shared_cfg_loader.load()
        shared_cfg = ManagerSharedConfig.model_validate(raw_shared_cfg)

        return cls(
            local=local_cfg,
            shared=shared_cfg,
            local_config_loader=local_cfg_loader,
            shared_config_loader=shared_cfg_loader,
            shared_config_watcher=EtcdConfigWatcher(shared_cfg_loader),
        )
