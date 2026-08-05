import asyncio
import fcntl
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

LOCK_DIR = Path("/run/backend.ai-coco")


@asynccontextmanager
async def host_lock(name: str, hold_seconds: float | None = None) -> AsyncIterator[None]:
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    handle = (LOCK_DIR / f"{name}.lock").open("w")

    def _yield_early() -> None:
        log.warning(
            "the {} host lock outlived its {} second window and was handed on while the holder"
            " still runs",
            name,
            hold_seconds,
        )
        handle.close()

    early: asyncio.TimerHandle | None = None
    try:
        await asyncio.to_thread(fcntl.flock, handle.fileno(), fcntl.LOCK_EX)
        if hold_seconds is not None:
            early = asyncio.get_running_loop().call_later(hold_seconds, _yield_early)
        yield
    finally:
        if early is not None:
            early.cancel()
        handle.close()
