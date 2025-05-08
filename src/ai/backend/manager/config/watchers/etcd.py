import asyncio
from contextlib import suppress
from typing import Any, Optional, Sequence, override

from aiotools import aclosing
from etcd_client import WatchEventType

from ai.backend.common.etcd import AsyncEtcd, Event
from ai.backend.common.types import QueueSentinel
from ai.backend.manager.config.watchers.types import AbstractConfigController, AbstractConfigWatcher


class EtcdConfigWatcher(AbstractConfigWatcher):
    _etcd: AsyncEtcd

    def __init__(self, etcd: AsyncEtcd) -> None:
        self._etcd = etcd

    async def watch(self) -> Any:
        async with aclosing(self._etcd.watch_prefix("config")) as agen:
            async for ev in agen:
                match ev:
                    case QueueSentinel.CLOSED | QueueSentinel.TIMEOUT:
                        break
                    case _:
                        if ev.event == WatchEventType.PUT:
                            yield ev


class EtcdConfigController(AbstractConfigController):
    _watcher: EtcdConfigWatcher
    _config: Any
    _task: Optional[asyncio.Task[None]]

    def __init__(self, watcher: EtcdConfigWatcher, config: Any) -> None:
        self._watcher = watcher
        self._config = config
        self._task = None

    def _update_target_attr(self, cfg: Any, path: Sequence[str], new_value: Any) -> None:
        *keys, last_key = path
        target = cfg

        # find the target object
        for key in keys:
            target = target[key] if isinstance(target, dict) else getattr(target, key)

        if isinstance(target, dict):
            target[last_key] = new_value
        else:
            setattr(target, last_key, new_value)

    def _handle_change_event(self, event: Event, cfg: Any) -> None:
        if event.event != WatchEventType.PUT:
            return

        key = event.key
        if key.startswith("config/"):
            key = key[len("config/") :]

        path_parts = [p for p in key.split("/") if p]
        self._update_target_attr(cfg, path_parts, event.value)

    async def _run(self) -> None:
        async for ev in self._watcher.watch():
            self._handle_change_event(ev, self._config)

    @override
    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    @override
    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None
