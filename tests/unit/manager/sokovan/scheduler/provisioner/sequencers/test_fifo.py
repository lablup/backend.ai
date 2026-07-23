"""Tests for the FIFO sequencer."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.fifo import FIFOSequencer
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.views.sokovan.workload import SessionWorkload

from .conftest import RESOURCE_GROUP_ID

WorkloadFactory = Callable[..., SessionWorkload]


class TestFIFOSequencer:
    @pytest.fixture
    def sequencer(self) -> FIFOSequencer:
        return FIFOSequencer()

    def test_name(self, sequencer: FIFOSequencer) -> None:
        assert sequencer.name == "FIFOSequencer"

    async def test_empty_workload(
        self,
        sequencer: FIFOSequencer,
        empty_snapshot: SystemSnapshot,
    ) -> None:
        result = await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, [])
        assert list(result) == []

    async def test_preserves_order(
        self,
        sequencer: FIFOSequencer,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        workloads = [workload_factory() for _ in range(5)]

        result = await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, workloads)

        assert list(result) == workloads
