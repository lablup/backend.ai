from __future__ import annotations

from pathlib import Path
from typing import Callable

import janus

from .asyncio import current_loop
from .types import Sentinel

__all__ = ("AsyncFileWriter",)


class AsyncFileWriter:
    """
    This class provides a context manager for making sequential async
    writes using janus queue.
    """

    def __init__(
        self,
        target_filename: str | Path,
        access_mode: str,
        encode: Callable[[str], bytes] = None,
        max_chunks: int = None,
    ) -> None:
        if max_chunks is None:
            max_chunks = 0
        self._q: janus.Queue[str | bytes | Sentinel] = janus.Queue(maxsize=max_chunks)
        self._target_filename = target_filename
        self._access_mode = access_mode
        self._binary_mode = "b" in access_mode
        if encode is not None:
            self._encode = encode
        else:
            self._encode = lambda v: v.encode()  # default encoder

    async def __aenter__(self):
        loop = current_loop()
        self._fut = loop.run_in_executor(None, self._write)
        return self

    def _write(self) -> None:
        with open(self._target_filename, self._access_mode) as f:
            while True:
                item = self._q.sync_q.get()
                if item is Sentinel.TOKEN:
                    break
                if self._binary_mode:
                    encoded = self._encode(item) if isinstance(item, str) else item
                    f.write(encoded)
                else:
                    f.write(item)
                self._q.sync_q.task_done()

    async def __aexit__(self, exc_type, exc, tb):
        await self._q.async_q.put(Sentinel.TOKEN)
        try:
            await self._fut
        finally:
            self._q.close()
            await self._q.wait_closed()

    async def write(self, item) -> None:
        await self._q.async_q.put(item)
