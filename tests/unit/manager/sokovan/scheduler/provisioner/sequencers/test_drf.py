"""Tests for the Dominant Resource Fairness (DRF) sequencer."""

from __future__ import annotations

import uuid
from collections.abc import Callable

import pytest

from ai.backend.common.identifier.user import UserID
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.drf import DRFSequencer
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.views.sokovan.workload import SessionWorkload

from .conftest import RESOURCE_GROUP_ID

WorkloadFactory = Callable[..., SessionWorkload]
SnapshotFactory = Callable[..., SystemSnapshot]


class TestDRFSequencer:
    @pytest.fixture
    def sequencer(self) -> DRFSequencer:
        return DRFSequencer()

    def test_name(self, sequencer: DRFSequencer) -> None:
        assert sequencer.name == "DRFSequencer"

    async def test_empty_workload(
        self,
        sequencer: DRFSequencer,
        empty_snapshot: SystemSnapshot,
    ) -> None:
        result = await sequencer.sequence(RESOURCE_GROUP_ID, empty_snapshot, [])
        assert list(result) == []

    async def test_single_user_workloads_keep_order(
        self,
        sequencer: DRFSequencer,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        """Workloads of a single user keep their input order (stable sort)."""
        user = UserID(uuid.uuid4())
        workloads = [workload_factory(user_id=user) for _ in range(3)]
        snapshot = snapshot_factory(
            capacities={"cpu": "100", "mem": "102400"},
            by_user={user: {"cpu": ("10", "0")}},
        )

        result = await sequencer.sequence(RESOURCE_GROUP_ID, snapshot, workloads)

        assert list(result) == workloads

    async def test_multiple_users_different_dominant_shares(
        self,
        sequencer: DRFSequencer,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        """The user with the lower dominant share is scheduled first."""
        heavy_user = UserID(uuid.uuid4())
        light_user = UserID(uuid.uuid4())
        heavy_workload = workload_factory(user_id=heavy_user)
        light_workload = workload_factory(user_id=light_user)
        snapshot = snapshot_factory(
            capacities={"cpu": "100", "mem": "102400"},
            by_user={
                # heavy: cpu share 0.5; light: cpu share 0.1
                heavy_user: {"cpu": ("30", "20")},
                light_user: {"cpu": ("10", "0")},
            },
        )

        result = await sequencer.sequence(
            RESOURCE_GROUP_ID, snapshot, [heavy_workload, light_workload]
        )

        assert list(result) == [light_workload, heavy_workload]

    async def test_dominant_share_is_max_over_slots(
        self,
        sequencer: DRFSequencer,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        """The dominant share is the maximum share across slot types."""
        cpu_heavy = UserID(uuid.uuid4())
        mem_heavy = UserID(uuid.uuid4())
        cpu_workload = workload_factory(user_id=cpu_heavy)
        mem_workload = workload_factory(user_id=mem_heavy)
        snapshot = snapshot_factory(
            capacities={"cpu": "100", "mem": "100000"},
            by_user={
                # cpu-heavy: cpu 0.6, mem 0.1 -> dominant 0.6
                cpu_heavy: {"cpu": ("60", "0"), "mem": ("10000", "0")},
                # mem-heavy: cpu 0.1, mem 0.4 -> dominant 0.4
                mem_heavy: {"cpu": ("10", "0"), "mem": ("40000", "0")},
            },
        )

        result = await sequencer.sequence(RESOURCE_GROUP_ID, snapshot, [cpu_workload, mem_workload])

        assert list(result) == [mem_workload, cpu_workload]

    async def test_new_user_gets_priority(
        self,
        sequencer: DRFSequencer,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        """A user with no recorded occupancy has dominant share zero."""
        existing_user = UserID(uuid.uuid4())
        new_user = UserID(uuid.uuid4())
        existing_workload = workload_factory(user_id=existing_user)
        new_workload = workload_factory(user_id=new_user)
        snapshot = snapshot_factory(
            capacities={"cpu": "100", "mem": "102400"},
            by_user={existing_user: {"cpu": ("50", "0")}},
        )

        result = await sequencer.sequence(
            RESOURCE_GROUP_ID, snapshot, [existing_workload, new_workload]
        )

        assert list(result) == [new_workload, existing_workload]

    async def test_zero_capacity_slot_is_skipped(
        self,
        sequencer: DRFSequencer,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        """Slots with zero capacity do not contribute to the dominant share."""
        user = UserID(uuid.uuid4())
        workload = workload_factory(user_id=user)
        snapshot = snapshot_factory(
            capacities={"cpu": "100", "cuda.shares": "0"},
            by_user={user: {"cuda.shares": ("4", "0")}},
        )

        result = await sequencer.sequence(RESOURCE_GROUP_ID, snapshot, [workload])

        assert list(result) == [workload]
