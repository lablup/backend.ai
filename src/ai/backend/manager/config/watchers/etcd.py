from typing import Any

from aiotools import aclosing
from etcd_client import WatchEventType

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import QueueSentinel
from ai.backend.manager.config.watchers.types import AbstractConfigWatcher


class EtcdConfigWatcher(AbstractConfigWatcher):
    _etcd: AsyncEtcd
    _config_prefix: str

    def __init__(self, etcd: AsyncEtcd, config_prefix: str = "ai/backend/config") -> None:
        self._etcd = etcd
        self._config_prefix = config_prefix

    async def watch(self) -> Any:
        async with aclosing(self._etcd.watch_prefix(self._config_prefix)) as agen:
            async for ev in agen:
                match ev:
                    case QueueSentinel.CLOSED | QueueSentinel.TIMEOUT:
                        break
                    case _:
                        if ev.event == WatchEventType.PUT:
                            yield ev
                        elif ev.event == WatchEventType.DELETE:
                            yield ev
