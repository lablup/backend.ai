from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Mapping

from async_timeout import timeout

from ai.backend.common.types import JSONSerializableMixin

from .defs import WatcherName
from .types import ProcResult

if TYPE_CHECKING:
    from .context import RootContext


async def _run_cmd(cmd: list[str]) -> ProcResult:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    raw_out, raw_err = await proc.communicate()
    out, err = raw_out.decode("utf8"), raw_err.decode("utf8")
    if err:
        result = ProcResult(False, err)
    else:
        result = ProcResult(True, out)
    return result


async def _run_cmd_timeout(cmd: list[str], timeout_sec: float) -> ProcResult:
    with timeout(timeout_sec):
        return await _run_cmd(cmd)


class BaseWatcher(metaclass=ABCMeta):
    name: ClassVar[WatcherName] = WatcherName("base")
    ctx: RootContext
    config: BaseWatcherConfig

    def __init__(self, ctx: RootContext, config: BaseWatcherConfig) -> None:
        self.ctx = ctx
        self.config = config

    @classmethod
    @abstractmethod
    def get_watcher_config_cls(cls) -> type[BaseWatcherConfig]:
        pass

    async def init(self) -> None:
        return

    async def shutdown(self) -> None:
        return

    async def run_cmd(
        self,
        cmd: list[str],
        *,
        timeout: float | None = None,
    ) -> ProcResult:
        if timeout is not None:
            return await _run_cmd_timeout(cmd, timeout)
        else:
            return await _run_cmd(cmd)


class BaseWatcherConfig(JSONSerializableMixin):
    @classmethod
    def from_json(cls, obj: Mapping[str, Any]) -> BaseWatcherConfig:
        return cls(**cls.as_trafaret().check(obj))
