"""Crash dumps for native faults that never reach Python exception handling."""

from __future__ import annotations

import faulthandler
import logging
import os
from pathlib import Path
from typing import IO, Final

from ai.backend.logging.utils import BraceStyleAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

# faulthandler writes through a raw file descriptor, so the file object must outlive the call.
_dump_file: IO[str] | None = None
# Tracked separately because a forked worker inherits the file of its supervisor.
_dump_pid: int | None = None


def enable_crash_dump(dump_dir: Path, tag: str) -> None:
    """Dump a Python traceback of every thread into `dump_dir` when the process
    receives SIGABRT, SIGSEGV, SIGBUS, SIGFPE, or SIGILL.
    Aborts from native extensions (e.g. a Rust panic at the FFI boundary) land here."""
    global _dump_file, _dump_pid
    pid = os.getpid()
    if _dump_pid == pid:
        return
    dump_path = dump_dir / f"crash-{tag}-{pid}.log"
    try:
        dump_dir.mkdir(parents=True, exist_ok=True)
        _dump_file = dump_path.open("a", buffering=1)
    except OSError as e:
        log.warning("could not open the crash dump file {}: {}", dump_path, e)
        return
    _dump_pid = pid
    faulthandler.enable(file=_dump_file, all_threads=True)
    log.debug("crash dumps enabled at {}", dump_path)
