"""Runs a supervisor in a subprocess and checks its exit code. Run directly, this module is
that supervisor."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from collections.abc import AsyncGenerator, Sequence
from enum import StrEnum
from typing import Any

import aiotools
import pytest

from ai.backend.common.process.child_exit import ChildExitMonitor, ChildStatus


class WorkerEnding(StrEnum):
    CLEAN = "clean"
    UNMARKED = "unmarked"
    KILLED = "killed"


@aiotools.server_context
async def worker(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    args: Sequence[Any],
) -> AsyncGenerator[None, signal.Signals]:
    ending: WorkerEnding = args[0]
    child_status: ChildStatus = args[1][pidx]
    child_status.publish_pid()
    if ending == WorkerEnding.KILLED:
        loop.call_later(0.5, os.kill, os.getpid(), signal.SIGKILL)
    yield
    if ending == WorkerEnding.CLEAN:
        child_status.mark_clean_shutdown()


def run_supervisor(ending: WorkerEnding) -> None:
    child_statuses = (ChildStatus(),)
    child_exit_monitor = ChildExitMonitor(child_statuses)
    aiotools.start_server(
        worker,
        main_ctxmgr=child_exit_monitor.main_context(),
        args=(ending, child_statuses),
        run_to_completion=ending != WorkerEnding.KILLED,
    )
    child_exit_monitor.raise_system_exit()


class TestChildExitMonitor:
    @pytest.mark.parametrize(
        ("ending", "expected_exit_code"),
        [
            (WorkerEnding.CLEAN, 0),
            (WorkerEnding.UNMARKED, 1),
            (WorkerEnding.KILLED, 1),
        ],
    )
    async def test_supervisor_exit_code(
        self, ending: WorkerEnding, expected_exit_code: int
    ) -> None:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            __file__,
            ending.value,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        assert proc.returncode == expected_exit_code, stderr.decode()


if __name__ == "__main__":
    run_supervisor(WorkerEnding(sys.argv[1]))
