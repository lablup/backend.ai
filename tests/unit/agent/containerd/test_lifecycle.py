from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from ai.backend.agent.containerd.client import ContainerRecord
from ai.backend.agent.containerd.lifecycle import (
    clean_container,
    destroy_container,
    launch_container,
)
from ai.backend.agent.containerd.profile.base import RuntimeOptions
from ai.backend.agent.errors.containerd import ContainerdOperationFailed

from .fakes import FakeContainerd

CID = "kernel-1-abcd1234"


def _record() -> ContainerRecord:
    return ContainerRecord(
        id=CID, image="img:1", snapshotter="overlayfs", snapshot_key=CID, labels={"k": "v"}
    )


async def _launch(fake: FakeContainerd) -> int:
    return await launch_container(
        fake,
        _record(),
        runtime="io.containerd.runc.v2",
        chain_id="sha256:aa",
        spec={"ociVersion": "1.1.0"},
        stdio="file:///scratch/task.log",
    )


class TestLaunch:
    async def test_runtime_options_reach_create_container(self, fake: FakeContainerd) -> None:
        options = RuntimeOptions(type_url="t", value=b"v")

        await launch_container(
            fake,
            _record(),
            runtime="io.containerd.kata.v2",
            chain_id="sha256:aa",
            spec={},
            stdio="",
            runtime_options=options,
        )

        assert fake.runtime_options[CID] == options

    async def test_runtime_options_default_to_none(self, fake: FakeContainerd) -> None:
        await _launch(fake)

        assert fake.runtime_options[CID] is None

    async def test_creates_snapshot_container_and_runs_the_task(self, fake: FakeContainerd) -> None:
        pid = await _launch(fake)

        assert pid == 1000
        assert [op for op, _ in fake.calls] == [
            "prepare_snapshot",
            "create_container",
            "create_task",
            "start_task",
        ]
        assert fake.snapshots[CID][0].options == ("lowerdir=sha256:aa",)
        assert fake.containers[CID].labels == {"k": "v"}

    @pytest.mark.parametrize("failing", ["create_container", "create_task", "start_task"])
    async def test_failure_removes_everything_created(
        self, failing: str, fake: FakeContainerd
    ) -> None:
        fake.failing.add(failing)

        with pytest.raises(ContainerdOperationFailed, match=failing):
            await _launch(fake)

        assert fake.snapshots == {}
        assert fake.containers == {}
        assert fake.tasks == {}

    async def test_failing_cleanup_does_not_hide_the_launch_error(
        self, fake: FakeContainerd
    ) -> None:
        fake.failing.update({"create_task", "remove_snapshot"})

        with pytest.raises(ContainerdOperationFailed, match="create_task"):
            await _launch(fake)

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


class TestDestroy:
    async def test_sigterm_stops_the_task_and_deletes_it(self, fake: FakeContainerd) -> None:
        await _launch(fake)

        assert await destroy_container(fake, CID, grace_sec=1.0) is True

        assert ("kill_task:SIGTERM", CID) in fake.calls
        assert ("kill_task:SIGKILL", CID) not in fake.calls
        assert CID not in fake.tasks
        assert CID in fake.containers  # clean_kernel removes the record

    async def test_sigkill_after_the_grace_period(self) -> None:
        fake = FakeContainerd(exits_on_sigterm=False)
        await _launch(fake)

        assert await destroy_container(fake, CID, grace_sec=0.2) is True

        assert [c for c in fake.calls if c[0].startswith("kill_task")] == [
            ("kill_task:SIGTERM", CID),
            ("kill_task:SIGKILL", CID),
        ]
        assert CID not in fake.tasks

    async def test_unknown_container_is_not_an_error(self, fake: FakeContainerd) -> None:
        assert await destroy_container(fake, "absent") is False

        assert fake.calls == []

    async def test_container_without_a_task_is_found(self, fake: FakeContainerd) -> None:
        fake.containers[CID] = _record()

        assert await destroy_container(fake, CID) is True

    async def test_already_stopped_task_is_only_deleted(self, fake: FakeContainerd) -> None:
        await _launch(fake)
        await fake.kill_task(CID, 9, all_processes=True)
        fake.calls.clear()

        assert await destroy_container(fake, CID) is True

        assert fake.calls == [("delete_task", CID)]


class TestClean:
    async def test_removes_task_container_and_snapshot(self, fake: FakeContainerd) -> None:
        await _launch(fake)

        await clean_container(fake, CID)

        assert fake.tasks == {}
        assert fake.containers == {}
        assert fake.snapshots == {}

    async def test_kills_a_running_task_first(self) -> None:
        fake = FakeContainerd(exits_on_sigterm=False)
        await _launch(fake)

        await clean_container(fake, CID)

        assert ("kill_task:SIGKILL", CID) in fake.calls
        assert fake.tasks == {}

    async def test_missing_everything_is_tolerated(self, fake: FakeContainerd) -> None:
        await clean_container(fake, "absent")
        await clean_container(fake, "absent")

        assert ("remove_snapshot", "absent") in fake.calls

    async def test_is_idempotent(self, fake: FakeContainerd) -> None:
        await _launch(fake)

        await clean_container(fake, CID)
        await clean_container(fake, CID)

        assert fake.containers == {}

    async def test_snapshot_key_comes_from_the_container_record(self, fake: FakeContainerd) -> None:
        fake.containers[CID] = ContainerRecord(
            id=CID, image="i", snapshotter="overlayfs", snapshot_key="other-key"
        )
        fake.snapshots["other-key"] = []

        await clean_container(fake, CID)

        assert fake.snapshots == {}

    async def test_explicit_snapshot_key_is_used_when_no_record_exists(
        self, fake: FakeContainerd
    ) -> None:
        fake.snapshots["snap-key"] = []

        await clean_container(fake, CID, snapshot_key="snap-key")

        assert fake.snapshots == {}
