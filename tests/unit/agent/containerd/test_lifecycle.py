from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.backend.agent.containerd import lifecycle
from ai.backend.agent.containerd.lifecycle import (
    clean_container,
    destroy_container,
    launch_container,
)
from ai.backend.agent.containerd.rpc.types import ContainerRecord
from ai.backend.agent.errors.containerd import ContainerdOperationFailed

from .fakes import FakeContainerd

CID = "kernel-1-abcd1234"


async def _launch(fake: FakeContainerd) -> int:
    record = ContainerRecord(CID, "img:1", "overlayfs", CID, {"k": "v"})
    return await launch_container(
        fake,
        record,
        runtime="io.containerd.runc.v2",
        chain_id="sha256:aa",
        spec={"ociVersion": "1.1.0"},
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

    async def test_failure_removes_everything_created(self, fake: FakeContainerd) -> None:
        fake.failing.add("start_task")

        with pytest.raises(ContainerdOperationFailed, match="start_task"):
            await _launch(fake)

        assert fake.snapshots == {} and fake.containers == {} and fake.tasks == {}


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
