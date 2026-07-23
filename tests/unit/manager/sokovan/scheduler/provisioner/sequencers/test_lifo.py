"""Tests for the LIFO sequencer."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.lifo import LIFOSequencer
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.views.sokovan.workload import SessionWorkload

from .conftest import RESOURCE_GROUP_ID

WorkloadFactory = Callable[..., SessionWorkload]


class TestLIFOSequencer:
    @pytest.fixture
    def sequencer(self) -> LIFOSequencer:
        return LIFOSequencer()

    def test_name(self, sequencer: LIFOSequencer) -> None:
        assert sequencer.name == "LIFOSequencer"

    async def test_empty_workload(
        self,
        sequencer: LIFOSequencer,
        empty_snapshot: SystemSnapshot,
    ) -> None:
        result = await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, [])
        assert list(result) == []

    async def test_reverses_order(
        self,
        sequencer: LIFOSequencer,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        workloads = [workload_factory() for _ in range(5)]

        result = await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, workloads)

        assert list(result) == list(reversed(workloads))

    async def test_single_workload(
        self,
        sequencer: LIFOSequencer,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        workload = workload_factory()

        result = await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, [workload])

        assert list(result) == [workload]
