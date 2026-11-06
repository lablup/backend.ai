from __future__ import annotations

import os
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import janus

from .asyncio import current_loop
from .types import Sentinel

__all__ = (
    "AsyncFileWriter",
    "open_dir_beneath",
)


class AsyncFileWriter:
    """
    This class provides a context manager for making sequential async
    writes using janus queue.
    """

    def __init__(
        self,
        target_filename: str | Path,
        access_mode: str,
        encode: Callable[[str], bytes] | None = None,
        max_chunks: int | None = None,
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

    async def __aenter__(self) -> AsyncFileWriter:
        loop = current_loop()
        self._fut = loop.run_in_executor(None, self._write)
        return self

    def _write(self) -> None:
        with Path(self._target_filename).open(self._access_mode) as f:
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

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any
    ) -> None:
        await self._q.async_q.put(Sentinel.TOKEN)
        try:
            await self._fut
        finally:
            self._q.close()
            await self._q.wait_closed()

    async def write(self, item: str | bytes) -> None:
        await self._q.async_q.put(item)


@contextmanager
def open_dir_beneath(
    root: Path,
    parts: Sequence[str],
    *,
    mkdir_mode: int | None = None,
    chmod_created: bool = False,
) -> Iterator[int]:
    """Open ``root``/``parts`` as a directory fd, refusing a symlink at any of ``parts``.

    ``mkdir_mode`` creates missing directories; ``chmod_created`` sets that mode past the umask.
    """
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            created = False
            if mkdir_mode is not None:
                try:
                    os.mkdir(part, mkdir_mode, dir_fd=fd)
                    created = True
                except FileExistsError:
                    pass
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
            if created and chmod_created and mkdir_mode is not None:
                os.fchmod(fd, mkdir_mode)
        yield fd
    finally:
        os.close(fd)
