import asyncio
import fcntl
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

LOCK_DIR = Path("/run/backend.ai-coco")


@asynccontextmanager
async def host_lock(name: str) -> AsyncIterator[None]:
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    handle = (LOCK_DIR / f"{name}.lock").open("w")
    try:
        await asyncio.to_thread(fcntl.flock, handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        handle.close()
