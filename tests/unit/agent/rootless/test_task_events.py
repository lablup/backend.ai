"""Container-death reporting for the enroot runtime.

containerd learns about a dead container from a daemon event stream; enroot has none, so the
runtime polls. The subtle part is not detecting the death — it is reporting it *once*. The agent
turns every 'exit' into a CLEAN lifecycle event, and the container stays in the runtime's tables
for the several seconds teardown takes, so a poller that re-derives "is it dead?" each tick keeps
firing for the whole window.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

import pytest

from ai.backend.agent.rootless.base import RootlessOciRuntime


@contextlib.asynccontextmanager
async def _consumer(runtime: RootlessOciRuntime) -> Any:
    """Run the poller in the background, yielding the list it appends to.

    One generator for the whole scenario, driven by a task rather than by cancelling
    ``__anext__`` — cancelling that leaves an async generator unusable, so a second read would
    only ever see StopAsyncIteration.
    """
    events: list[Any] = []

    async def consume() -> None:
        async for event in runtime.subscribe_task_events():
            events.append(event)

    task = asyncio.create_task(consume())
    try:
        yield events
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def _settle() -> None:
    """Long enough for several poll ticks at the interval the tests set."""
    await asyncio.sleep(0.15)


class TestExitReporting:
    async def test_a_death_is_reported_exactly_once(
        self, runtime: RootlessOciRuntime, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The container stays in `_pids` until remove_container clears it — several seconds after
        the process is gone. Re-firing across that window produced 4 CLEAN events for one death,
        and the duplicates raced the first, recording the kernel as `already-terminated` instead of
        `self-terminated`."""
        monkeypatch.setattr(
            "ai.backend.agent.rootless.base.TASK_POLL_INTERVAL_SEC", 0.01, raising=False
        )
        runtime._pids["dead"] = 424242
        monkeypatch.setattr(runtime, "_alive", lambda pid: False)

        async with _consumer(runtime) as events:
            await _settle()

        assert [e.container_id for e in events] == ["dead"]

    async def test_a_live_container_is_not_reported(
        self, runtime: RootlessOciRuntime, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "ai.backend.agent.rootless.base.TASK_POLL_INTERVAL_SEC", 0.01, raising=False
        )
        runtime._pids["alive"] = 424242
        monkeypatch.setattr(runtime, "_alive", lambda pid: True)

        async with _consumer(runtime) as events:
            await _settle()

        assert events == []

    async def test_each_container_is_reported_on_its_own(
        self, runtime: RootlessOciRuntime, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "ai.backend.agent.rootless.base.TASK_POLL_INTERVAL_SEC", 0.01, raising=False
        )
        runtime._pids.update({"a": 1, "b": 2})
        monkeypatch.setattr(runtime, "_alive", lambda pid: pid != 1)

        async with _consumer(runtime) as events:
            await _settle()
            assert [e.container_id for e in events] == ["a"]
            # `b` dies later and must still be reported, even though `a` is already suppressed.
            monkeypatch.setattr(runtime, "_alive", lambda pid: False)
            await _settle()

        assert [e.container_id for e in events] == ["a", "b"]


class TestExitCode:
    def test_unknown_when_the_container_was_not_ours(self, runtime: RootlessOciRuntime) -> None:
        """A container recovered from the journal after an agent restart is not our child, so
        there is no status to collect. Reporting 0 would turn a crash into a clean exit."""
        runtime._pids["recovered"] = 1
        assert runtime._exit_code_of("recovered") == -1

    def test_unknown_while_the_process_is_still_being_reaped(
        self, runtime: RootlessOciRuntime
    ) -> None:
        class _Unreaped:
            returncode = None

        runtime._procs["c"] = _Unreaped()  # type: ignore[assignment]
        assert runtime._exit_code_of("c") == -1

    def test_the_real_status_once_it_is_known(self, runtime: RootlessOciRuntime) -> None:
        class _Exited:
            returncode = 137

        runtime._procs["c"] = _Exited()  # type: ignore[assignment]
        assert runtime._exit_code_of("c") == 137
