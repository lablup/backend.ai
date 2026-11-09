from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.agent.containerd import lifecycle
from ai.backend.agent.containerd.lifecycle import (
    clean_container,
    destroy_container,
    launch_container,
)
from ai.backend.agent.containerd.rpc.types import ContainerRecord, RuntimeOptions
from ai.backend.agent.errors.containerd import ContainerdOperationFailed

from .fakes import FakeContainerd

CID = "kernel-1-abcd1234"


async def _launch(fake: FakeContainerd, options: RuntimeOptions | None = None) -> int:
    record = ContainerRecord(CID, "img:1", "overlayfs", CID, {"k": "v"})
    return await launch_container(
        fake,
        record,
        runtime="io.containerd.runc.v2",
        chain_id="sha256:aa",
        spec={"ociVersion": "1.1.0"},
        runtime_options=options,
    )


class TestLaunch:
    async def test_creates_snapshot_container_and_runs_the_task(self, fake: FakeContainerd) -> None:
        assert await _launch(fake) == 1000

        assert fake.calls == [
            "prepare_snapshot",
            "create_container",
            "create_task",
            "start_task",
        ]

    async def test_runtime_options_reach_container_creation(self, fake: FakeContainerd) -> None:
        options = RuntimeOptions(type_url="t/1", value=b"v")

        await _launch(fake, options)

        assert fake.runtime_options[CID] == options

    async def test_failure_removes_everything_created(self, fake: FakeContainerd) -> None:
        fake.failing.add("start_task")

        with pytest.raises(ContainerdOperationFailed, match="start_task"):
            await _launch(fake)

        assert fake.snapshots == {} and fake.containers == {} and fake.tasks == {}

    @pytest.mark.parametrize(
        "cancelled_op", ["prepare_snapshot", "create_container", "create_task"]
    )
    async def test_cancellation_removes_everything_created(
        self, cancelled_op: str, fake: FakeContainerd
    ) -> None:
        """A cancel that lands after the daemon did the step leaves nothing behind."""
        step: Callable[..., Awaitable[Any]] = getattr(fake, cancelled_op)

        async def done_then_cancelled(*args: Any, **kwargs: Any) -> Any:
            await step(*args, **kwargs)
            raise asyncio.CancelledError

        setattr(fake, cancelled_op, done_then_cancelled)

        with pytest.raises(asyncio.CancelledError):
            await _launch(fake)

        assert fake.snapshots == {}
        assert fake.containers == {}
        assert fake.tasks == {}

    async def test_task_cancelled_while_a_step_is_blocked_leaves_nothing(
        self, fake: FakeContainerd, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        entered = asyncio.Event()

        async def blocked(*args: Any, **kwargs: Any) -> int:
            entered.set()
            await asyncio.Event().wait()
            return 0

        monkeypatch.setattr(fake, "create_task", blocked)
        launch = asyncio.create_task(_launch(fake))
        await entered.wait()

        launch.cancel()
        with pytest.raises(asyncio.CancelledError):
            await launch

        assert fake.snapshots == {}
        assert fake.containers == {}
        assert fake.tasks == {}


class TestDestroy:
    @pytest.mark.parametrize("exits_on_sigterm", [True, False])
    async def test_stops_the_task_with_sigkill_only_after_the_grace_period(
        self, exits_on_sigterm: bool
    ) -> None:
        fake = FakeContainerd(exits_on_sigterm=exits_on_sigterm)
        await _launch(fake)

        assert await destroy_container(fake, CID, grace_sec=0.2) is True

        assert ("kill_task:SIGKILL" in fake.calls) is not exits_on_sigterm
        assert CID not in fake.tasks and CID in fake.containers

    async def test_task_surviving_sigkill_is_an_error(
        self, fake: FakeContainerd, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await _launch(fake)
        monkeypatch.setattr(lifecycle, "KILL_WAIT_SEC", 0.2)
        monkeypatch.setattr(fake, "kill_task", AsyncMock())

        with pytest.raises(ContainerdOperationFailed, match="after SIGKILL"):
            await destroy_container(fake, CID, grace_sec=0.1)


class TestClean:
    async def test_removes_everything_and_tolerates_missing(self, fake: FakeContainerd) -> None:
        await _launch(fake)

        await clean_container(fake, CID)
        await clean_container(fake, CID)

        assert fake.tasks == {} and fake.containers == {} and fake.snapshots == {}

    async def test_failing_task_deletion_keeps_the_container_record_and_snapshot(
        self, fake: FakeContainerd
    ) -> None:
        """The record is the way to the task: a task that is not confirmed gone keeps it."""
        await _launch(fake)
        fake.failing.add("delete_task")

        with pytest.raises(ContainerdOperationFailed, match="delete_task"):
            await clean_container(fake, CID)

        assert CID in fake.containers
        assert CID in fake.snapshots

    async def test_task_surviving_sigkill_keeps_the_container_record_and_snapshot(
        self, fake: FakeContainerd, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await _launch(fake)
        monkeypatch.setattr(lifecycle, "KILL_WAIT_SEC", 0.2)

        async def ignored(*args: Any, **kwargs: Any) -> None:
            return None

        monkeypatch.setattr(fake, "kill_task", ignored)

        with pytest.raises(ContainerdOperationFailed, match="did not exit"):
            await clean_container(fake, CID)

        assert CID in fake.containers
        assert CID in fake.snapshots

    async def test_failing_container_deletion_still_removes_the_snapshot(
        self, fake: FakeContainerd
    ) -> None:
        await _launch(fake)
        fake.failing.add("delete_container")

        with pytest.raises(ContainerdOperationFailed, match="delete_container"):
            await clean_container(fake, CID)

        assert fake.tasks == {}
        assert fake.snapshots == {}
