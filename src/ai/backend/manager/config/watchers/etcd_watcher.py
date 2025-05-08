from typing import Any

from aiotools import aclosing
from etcd_client import WatchEventType

from ai.backend.common.types import QueueSentinel
from ai.backend.manager.config.loader.etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.watchers.types import AbstractConfigWatcher


class EtcdConfigWatcher(AbstractConfigWatcher):
    _etcd_loader: LegacyEtcdLoader

    def __init__(self, etcd_loader: LegacyEtcdLoader):
        self._etcd_loader = etcd_loader

    async def watch(self) -> Any:
        async with aclosing(self._etcd_loader._etcd.watch_prefix("config")) as agen:
            async for ev in agen:
                match ev:
                    case QueueSentinel.CLOSED | QueueSentinel.TIMEOUT:
                        break
                    case _:
                        if ev.event == WatchEventType.PUT:
                            yield await self._etcd_loader.load()
