import asyncio
import fcntl
import logging
import time
from pathlib import Path

from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))


class FileLock:
    default_timeout: int = 3  # not allow infinite timeout for safety
    locked: bool = False

    def __init__(self, path: Path, *, mode: str = "rb", timeout: int = None):
        self._path = path
        self._mode = mode
        self._timeout = timeout if timeout is not None else self.default_timeout

    async def __aenter__(self):
        def _lock():
            start_time = time.perf_counter()
            self._fp = open(self._path, self._mode)
            while True:
                try:
                    fcntl.flock(self._fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.locked = True
                    log.debug("file lock acquired: {}", self._path)
                    return self._fp
                except BlockingIOError:
                    # Failed to get file lock. Waiting until timeout ...
                    if time.perf_counter() - start_time > self._timeout:
                        raise TimeoutError(f"failed to lock file: {self._path}")
                time.sleep(0.1)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _lock)

    async def __aexit__(self, *args):
        def _unlock():
            if self.locked:
                fcntl.flock(self._fp, fcntl.LOCK_UN)
                self.locked = False
                log.debug("file lock released: {}", self._path)
            self._fp.close()
            self.f_fp = None

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _unlock)
