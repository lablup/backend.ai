from __future__ import annotations

import logging
from contextlib import asynccontextmanager as actxmgr
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Final,
)

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import (
    EventDispatcher,
    EventProducer,
)
from ai.backend.common.logging import BraceStyleAdapter

from .defs import WatcherName
from .exception import InvalidWatcher

if TYPE_CHECKING:
    from .base import BaseWatcher, BaseWatcherConfig


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

EVENT_DISPATCHER_CONSUMER_GROUP: Final = "storage-proxy-watcher"


class RootContext:
    pid: int
    pidx: int
    etcd: AsyncEtcd
    local_config: dict[str, Any]
    dsn: str | None
    event_producer: EventProducer | None
    event_dispatcher: EventDispatcher | None
    _watchers: dict[WatcherName, tuple[type[BaseWatcher], BaseWatcherConfig]]

    def __init__(
        self,
        pid: int,
        pidx: int,
        node_id: str,
        local_config: dict[str, Any],
        etcd: AsyncEtcd,
        *,
        event_producer: EventProducer | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.pid = pid
        self.pidx = pidx
        self.node_id = node_id
        self.etcd = etcd
        self.local_config = local_config
        self.event_producer = event_producer
        self.event_dispatcher = event_dispatcher
        self._watchers = {}

    async def __aenter__(self) -> None:
        pass

    async def __aexit__(self, *exc_info) -> bool | None:
        pass

    def register_watcher(self, watcher_cls: type[BaseWatcher], config: BaseWatcherConfig) -> None:
        self._watchers[watcher_cls.name] = (watcher_cls, config)

    @actxmgr
    async def get_watcher(self, name: WatcherName) -> AsyncIterator[BaseWatcher]:
        try:
            watcher_cls, config = self._watchers[name]
        except KeyError:
            raise InvalidWatcher(f"Watcher with name {name} not found")

        watcher = watcher_cls(self, config)

        await watcher.init()
        try:
            yield watcher
        finally:
            await watcher.shutdown()
