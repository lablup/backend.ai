"""Tests for SchedulingSequencer (strategy pool + priority banding)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping

import pytest

from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.drf import DRFSequencer
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.fifo import FIFOSequencer
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.lifo import LIFOSequencer
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.sequencer import (
    SchedulingSequencer,
    WorkloadSequencer,
)
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.views.sokovan.workload import SessionWorkload

from .conftest import RESOURCE_GROUP_ID

WorkloadFactory = Callable[..., SessionWorkload]


def _pool() -> Mapping[str, WorkloadSequencer]:
    pool: dict[str, WorkloadSequencer] = defaultdict(DRFSequencer)
    pool["fifo"] = FIFOSequencer()
    pool["lifo"] = LIFOSequencer()
    pool["drf"] = DRFSequencer()
    return pool


class TestSchedulingSequencer:
    @pytest.fixture
    def sequencer(self) -> SchedulingSequencer:
        return SchedulingSequencer(_pool())

    def test_strategy_name_picks_from_pool(self, sequencer: SchedulingSequencer) -> None:
        assert sequencer.strategy_name("fifo") == "FIFOSequencer"
        assert sequencer.strategy_name("lifo") == "LIFOSequencer"

    def test_unknown_scheduler_falls_back_to_default(self, sequencer: SchedulingSequencer) -> None:
        assert sequencer.strategy_name("no-such-scheduler") == "DRFSequencer"

    def test_strategy_success_message(self, sequencer: SchedulingSequencer) -> None:
        assert sequencer.strategy_success_message("fifo") == (
            "Sessions sequenced in first-in-first-out order"
        )

    async def test_empty_workloads(
        self,
        sequencer: SchedulingSequencer,
        empty_snapshot: SystemSnapshot,
    ) -> None:
        result = await sequencer.sequence("fifo", RESOURCE_GROUP_ID, empty_snapshot, [])
        assert list(result) == []

    async def test_keeps_all_workloads_across_priorities(
        self,
        sequencer: SchedulingSequencer,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        workloads = [workload_factory(priority=i % 3) for i in range(6)]

        result = await sequencer.sequence("fifo", RESOURCE_GROUP_ID, empty_snapshot, workloads)

        assert sorted(w.meta.session_id for w in result) == sorted(
            w.meta.session_id for w in workloads
        )

    async def test_orders_by_descending_priority(
        self,
        sequencer: SchedulingSequencer,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        low = workload_factory(priority=1)
        high = workload_factory(priority=10)
        mid = workload_factory(priority=5)

        result = await sequencer.sequence(
            "fifo", RESOURCE_GROUP_ID, empty_snapshot, [low, high, mid]
        )

        assert [w.priority for w in result] == [10, 5, 1]

    async def test_preserves_order_within_same_priority(
        self,
        sequencer: SchedulingSequencer,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        first = workload_factory(priority=5)
        second = workload_factory(priority=5)
        third = workload_factory(priority=5)

        result = await sequencer.sequence(
            "fifo", RESOURCE_GROUP_ID, empty_snapshot, [first, second, third]
        )

        assert list(result) == [first, second, third]

    async def test_strategy_applies_within_priority_band(
        self,
        sequencer: SchedulingSequencer,
        empty_snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        """LIFO reverses within a band, but priority still dominates."""
        low_a = workload_factory(priority=1)
        low_b = workload_factory(priority=1)
        high_a = workload_factory(priority=9)
        high_b = workload_factory(priority=9)

        result = await sequencer.sequence(
            "lifo", RESOURCE_GROUP_ID, empty_snapshot, [low_a, low_b, high_a, high_b]
        )

        assert list(result) == [high_b, high_a, low_b, low_a]
