from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pyroscope

if TYPE_CHECKING:
    from ai.backend.common.configs.memray import MemrayConfig

__all__ = (
    "PyroscopeArgs",
    "Profiler",
    "start_memray_tracker",
    "close_memray_tracker_in_worker",
)


@dataclass
class PyroscopeArgs:
    enabled: bool
    application_name: str | None
    server_address: str | None
    sample_rate: int | None


class Profiler:
    def __init__(self, pyroscope_args: PyroscopeArgs) -> None:
        if pyroscope_args.enabled:
            pyroscope.configure(
                application_name=pyroscope_args.application_name,
                server_address=pyroscope_args.server_address,
                sample_rate=pyroscope_args.sample_rate,
            )


_memray_tracker: contextlib.AbstractContextManager[Any] | None = None


def start_memray_tracker(
    config: MemrayConfig,
) -> contextlib.AbstractContextManager[Any] | None:
    """Start memray allocation tracking in the current process, if enabled.

    Call this from the master process *before* it forks its service workers.
    `follow_fork=True` makes each forked worker capture into its own file, which
    is what we actually want to look at -- the workers do the real work.

    The caller owns the returned tracker and must close it (see the module note
    on why the workers cannot rely on the master's close).
    """
    global _memray_tracker
    if not config.enabled:
        return None

    import memray

    # Suffix the PID so a restart cannot collide with an earlier capture, which
    # memray would refuse to overwrite.
    destination = config.output_destination
    destination = destination.with_name(f"{destination.stem}.{os.getpid()}{destination.suffix}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    _memray_tracker = memray.Tracker(
        destination,
        follow_fork=True,
        native_traces=config.native_traces,
    )
    _memray_tracker.__enter__()
    return _memray_tracker


def close_memray_tracker_in_worker() -> None:
    """Close the forked worker's own memray capture.

    Call this from the worker's *shutdown path* -- after its server context has
    exited, while the worker is still running Python.

    Without this the worker's capture -- the only one worth reading, since the
    workers do the real work -- is never closed and ends up truncated and
    unparseable: memray stops at the first bad record, reporting a ~0s span out
    of a multi-hundred-MB file.

    An `atexit` handler does *not* work here. `aiotools` ends its forked
    children with a bare `os._exit()` (see `aiotools/fork.py`), which runs
    neither `atexit` handlers nor interpreter finalization -- and memray's
    `Tracker` writes the capture's trailer only from `__exit__` (it has no
    `__del__` and registers no `atexit` of its own). So the worker has to close
    the tracker itself, explicitly, before it returns.

    The global is a per-process copy (we are in a fork), so clearing it here does
    not disturb the master, which closes its own tracker separately.
    """
    global _memray_tracker
    if _memray_tracker is None:
        return
    _memray_tracker.__exit__(None, None, None)
    _memray_tracker = None
