"""Detection of child processes that die without going through the shutdown path."""

from __future__ import annotations

import logging
import multiprocessing as mp
import os
import signal
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from multiprocessing.sharedctypes import Synchronized
from multiprocessing.synchronize import Event as MPEvent
from typing import Final

from ai.backend.logging.utils import BraceStyleAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_POLL_INTERVAL: Final[float] = 0.05
_UNPUBLISHED_PID: Final[int] = 0


@dataclass(frozen=True)
class ChildExit:
    pid: int
    si_code: int
    si_status: int

    def describe(self) -> str:
        match self.si_code:
            case os.CLD_KILLED | os.CLD_DUMPED:
                return f"was killed by {signal.Signals(self.si_status).name}"
            case os.CLD_EXITED:
                return f"exited with code {self.si_status}"
            case _:
                return f"exited with si_code={self.si_code}, si_status={self.si_status}"


@dataclass(frozen=True)
class ChildCheck:
    """Whether the child has ended, and how it ended while the exit status is still
    available. aiotools may have reaped the status already, leaving only the fact."""

    ended: bool
    child_exit: ChildExit | None = None


@dataclass(frozen=True)
class ChildStatus:
    """One child's process ID and whether it reached the end of its shutdown path.
    Both live in shared memory because the child writes them and the supervisor reads
    them. Create one per child and hand it to that child through the worker arguments."""

    pid: Synchronized[int] = field(
        default_factory=lambda: mp.Value("i", _UNPUBLISHED_PID),
    )
    clean_shutdown: MPEvent = field(default_factory=mp.Event)

    def publish_pid(self) -> None:
        """Call once the child process has started."""
        self.pid.value = os.getpid()

    def mark_clean_shutdown(self) -> None:
        """Call once the child has finished its shutdown routines."""
        self.clean_shutdown.set()


class ChildExitMonitor:
    """Turn a child that stopped without being asked to into a non-zero exit code, and
    shut the supervisor down if nothing else does. `aiotools.start_server()` keeps the
    parent alive when a worker dies, so the service manager sees a healthy unit that no
    longer serves anything."""

    _statuses: Final[Sequence[ChildStatus]]
    _armed: Final[threading.Event]
    _thread: threading.Thread | None

    def __init__(self, statuses: Sequence[ChildStatus]) -> None:
        self._statuses = statuses
        self._armed = threading.Event()
        self._thread = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._armed.set()
        self._thread = threading.Thread(
            target=self._observe, name="child-exit-monitor", daemon=True
        )
        self._thread.start()

    def raise_system_exit(self) -> None:
        """Fail the process unless every child ran its shutdown routines. Call this once
        the server has stopped: a zero exit code tells a service manager that the stop
        was intended, so `Restart=on-failure` would not fire."""
        if all(status.clean_shutdown.is_set() for status in self._statuses):
            return
        raise SystemExit(1)

    def disarm(self) -> None:
        """Stop watching, so an expected shutdown does not draw a redundant signal."""
        self._armed.clear()

    def _observe(self) -> None:
        # Watching for a child's presence rather than reaping its exit status: aiotools
        # reaps through its own pidfd reader, and a second reaper would race it for the
        # single status the kernel keeps. Presence cannot be consumed by anyone else, and
        # whether the stop was intended is answered by the flag the child sets, not here.
        while self._armed.is_set():
            time.sleep(_POLL_INTERVAL)
            for status in self._statuses:
                pid = status.pid.value
                if pid == _UNPUBLISHED_PID:
                    continue
                check = self._check_ended(pid)
                if not check.ended or status.clean_shutdown.is_set():
                    continue
                self._request_shutdown(pid, check.child_exit)
                return

    def _check_ended(self, pid: int) -> ChildCheck:
        """`WNOWAIT` keeps this check from consuming the exit status, so that aiotools
        can still reap the child itself."""
        try:
            info = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOWAIT | os.WNOHANG)
        except ChildProcessError:
            return ChildCheck(ended=True)
        except OSError as e:
            log.warning("stopped watching the child process {}: {}", pid, e)
            return ChildCheck(ended=False)
        if info is None:
            return ChildCheck(ended=False)
        return ChildCheck(
            ended=True,
            child_exit=ChildExit(info.si_pid, info.si_code, info.si_status),
        )

    def _request_shutdown(self, pid: int, child_exit: ChildExit | None) -> None:
        log.error(
            "The child process {} {} without being asked to stop. Shutting down the "
            "supervisor so that the service manager can restart it.",
            pid,
            child_exit.describe() if child_exit is not None else "terminated",
        )
        # Go through the stop signal the supervisor already handles, so that the
        # remaining shutdown routines still run.
        os.kill(os.getpid(), signal.SIGINT)
