import argparse
import asyncio
import errno
import logging
import mmap
import multiprocessing
import os
import sys
import time
from collections.abc import AsyncIterator, Sequence
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, TextIO

from ai.backend.accelerator.dax import __version__
from ai.backend.accelerator.dax.discovery import read_device
from ai.backend.accelerator.dax.errors import DAXDeviceNotFound, DAXScrubError
from ai.backend.common.json import dump_json_str
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

MODE_FULL: Final[str] = "full"
MODE_HEADER_ONLY: Final[str] = "header-only"
CHUNK_TARGET_BYTES: Final[int] = 256 * 1024 * 1024
FLUSH_UNSUPPORTED_ERRNOS: Final[frozenset[int]] = frozenset({
    errno.EINVAL,
    errno.ENOTSUP,
    errno.EOPNOTSUPP,
})


def flush_mapping(mm: mmap.mmap) -> None:
    """`msync` the mapping, tolerating device classes that reject it.

    Device-DAX has no writeback path, so `msync` returns `EINVAL` and stores are
    already persistent without it.
    """
    try:
        mm.flush()
    except OSError as e:
        if e.errno not in FLUSH_UNSUPPORTED_ERRNOS:
            raise


def zero_range(path: str, start: int, end: int, align: int) -> int:
    """Zero `[start, end)` through `MAP_SHARED` mappings of at most one chunk each."""
    chunk_size = max(align, CHUNK_TARGET_BYTES // align * align)
    zeros = bytes(chunk_size)
    written = 0
    fd = os.open(path, os.O_RDWR)
    try:
        for offset in range(start, end, chunk_size):
            length = min(chunk_size, end - offset)
            with mmap.mmap(fd, length, flags=mmap.MAP_SHARED, offset=offset) as mm:
                mm[:length] = memoryview(zeros)[:length]
                flush_mapping(mm)
            written += length
    finally:
        os.close(fd)
    return written


def is_zeroed(path: str, offset: int, length: int) -> bool:
    fd = os.open(path, os.O_RDONLY)
    try:
        with mmap.mmap(fd, length, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ, offset=offset) as mm:
            return mm[:length] == bytes(length)
    finally:
        os.close(fd)


def _probe() -> bool:
    return True


@asynccontextmanager
async def open_executor(workers: int) -> AsyncIterator[Executor]:
    """A spawn-context process pool, or a thread pool where spawning fails."""
    loop = asyncio.get_running_loop()
    executor: Executor
    process_pool: ProcessPoolExecutor | None = None
    try:
        process_pool = ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context("spawn"))
        await loop.run_in_executor(process_pool, _probe)
        executor = process_pool
    except Exception as e:
        log.warning("process pool unavailable, falling back to threads: {!r}", e)
        if process_pool is not None:
            process_pool.shutdown(wait=False, cancel_futures=True)
        executor = ThreadPoolExecutor(workers)
    try:
        yield executor
    finally:
        await asyncio.to_thread(executor.shutdown, wait=True)


def _stripes(total: int, align: int, workers: int) -> list[tuple[int, int]]:
    units = total // align
    count = max(1, min(workers, units))
    units_per_stripe = -(-units // count)
    return [
        (i * units_per_stripe * align, min(units, (i + 1) * units_per_stripe) * align)
        for i in range(count)
        if i * units_per_stripe < units
    ]


async def scrub_device(
    executor: Executor,
    sysfs_root: Path,
    path: str,
    *,
    header_only: bool,
    workers: int,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "time_utc": datetime.now(UTC).isoformat(),
        "device_id": None,
        "serials": [],
        "path": path,
        "size": None,
        "align": None,
        "mode": MODE_HEADER_ONLY if header_only else MODE_FULL,
        "bytes_written": 0,
        "seconds": 0.0,
        "bytes_per_sec": 0.0,
        "verified": False,
        "result": "error",
        "error": None,
        "tool_revision": __version__,
    }
    loop = asyncio.get_running_loop()
    started = time.monotonic()
    try:
        info = read_device(sysfs_root, Path(path).name, allow_non_cxl=True)
        if info is None:
            raise DAXDeviceNotFound(f"no dax device in sysfs for {path}")
        record.update(device_id=info.device_id, serials=list(info.serials))
        record.update(size=info.size, align=info.align)
        if info.align <= 0 or info.size <= 0 or info.size % info.align != 0:
            raise DAXScrubError(f"size {info.size} is not a positive multiple of {info.align}")
        end = info.align if header_only else info.size
        results = await asyncio.gather(
            *(
                loop.run_in_executor(executor, zero_range, path, start, stop, info.align)
                for start, stop in _stripes(end, info.align, workers)
            )
        )
        record["bytes_written"] = sum(results)
        check_offsets = [0] if header_only else [0, info.size - info.align]
        verified = True
        for offset in check_offsets:
            zeroed = await loop.run_in_executor(None, is_zeroed, path, offset, info.align)
            verified = verified and zeroed
        record["verified"] = verified
        if not verified:
            raise DAXScrubError(f"read-back of {path} is not all zero")
        record["result"] = "ok"
    except Exception as e:
        record["error"] = str(e)
    seconds = time.monotonic() - started
    record["seconds"] = seconds
    record["bytes_per_sec"] = record["bytes_written"] / seconds if seconds > 0 else 0.0
    return record


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m ai.backend.accelerator.dax.scrub",
        description="Zero device-DAX devices and print one JSON record per path.",
    )
    parser.add_argument("paths", nargs="+", metavar="PATH")
    parser.add_argument("--header-only", action="store_true")
    parser.add_argument("--sysfs-root", type=Path, default=Path("/sys"))
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args(argv)


async def run(argv: Sequence[str], out: TextIO) -> int:
    """Scrub every path in `argv`; returns 0 only if every record is ok."""
    args = _parse_args(argv)
    workers = max(1, args.workers)
    all_ok = True
    async with open_executor(workers) as executor:
        for path in args.paths:
            record = await scrub_device(
                executor,
                args.sysfs_root,
                path,
                header_only=args.header_only,
                workers=workers,
            )
            out.write(dump_json_str(record) + "\n")
            out.flush()
            all_ok = all_ok and record["result"] == "ok"
    return 0 if all_ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    return asyncio.run(run(sys.argv[1:] if argv is None else argv, sys.stdout))


if __name__ == "__main__":
    sys.exit(main())
