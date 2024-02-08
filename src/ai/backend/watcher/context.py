from __future__ import annotations

import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
)

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.logging import BraceStyleAdapter

from .defs import WatcherName
from .exception import InvalidWatcher
from .plugin import WatcherWebAppPluginContext

if TYPE_CHECKING:
    from .base import BaseWatcher


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "storage-proxy-watcher"


class RootContext:
    pid: int
    pidx: int
    etcd: AsyncEtcd
    local_config: dict[str, Any]
    dsn: str | None
    _watchers: dict[WatcherName, BaseWatcher]
    webapp_ctx: WatcherWebAppPluginContext | None

    def __init__(
        self,
        pid: int,
        pidx: int,
        node_id: str,
        local_config: dict[str, Any],
        etcd: AsyncEtcd,
    ) -> None:
        self.pid = pid
        self.pidx = pidx
        self.node_id = node_id
        self.etcd = etcd
        self.local_config = local_config
        self._watchers = {}
        self.webapp_ctx = None

    async def __aenter__(self) -> None:
        pass

    async def __aexit__(self, *exc_info) -> bool | None:
        pass

    def register_watcher(self, watcher: BaseWatcher) -> None:
        if (watcher_name := watcher.name) in self._watchers:
            raise TypeError(f"Duplicate watcher name. `{watcher_name}` already registered.")
        self._watchers[watcher_name] = watcher

    def get_watcher(self, name: WatcherName) -> BaseWatcher:
        try:
            watcher = self._watchers[name]
        except KeyError:
            raise InvalidWatcher(f"Watcher with name {name} not found")

        return watcher
