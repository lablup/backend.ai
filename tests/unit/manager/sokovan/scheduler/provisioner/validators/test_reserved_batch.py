"""Tests for the reserved batch session validator."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import SessionTypes
from ai.backend.manager.sokovan.scheduler.provisioner.validators.exceptions import (
    ReservedBatchSessionNotReady,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.reserved_batch import (
    ReservedBatchSessionValidator,
)
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot

from .conftest import SnapshotFactory, WorkloadFactory


class TestReservedBatchSessionValidator:
    @pytest.fixture
    def validator(self) -> ReservedBatchSessionValidator:
        return ReservedBatchSessionValidator()

    @pytest.fixture
    def snapshot(self, snapshot_factory: SnapshotFactory) -> SystemSnapshot:
        return snapshot_factory()

    def test_non_batch_session_passes(
        self,
        validator: ReservedBatchSessionValidator,
        snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        workload = workload_factory(
            session_type=SessionTypes.INTERACTIVE,
            starts_at=datetime.now(tzutc()) + timedelta(hours=1),
        )

        validator.validate(snapshot, workload)

    def test_batch_session_without_start_time_passes(
        self,
        validator: ReservedBatchSessionValidator,
        snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        workload = workload_factory(session_type=SessionTypes.BATCH, starts_at=None)

        validator.validate(snapshot, workload)

    def test_batch_session_after_start_time_passes(
        self,
        validator: ReservedBatchSessionValidator,
        snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        workload = workload_factory(
            session_type=SessionTypes.BATCH,
            starts_at=datetime.now(tzutc()) - timedelta(minutes=5),
        )

        validator.validate(snapshot, workload)

    def test_batch_session_before_start_time_fails(
        self,
        validator: ReservedBatchSessionValidator,
        snapshot: SystemSnapshot,
        workload_factory: WorkloadFactory,
    ) -> None:
        workload = workload_factory(
            session_type=SessionTypes.BATCH,
            starts_at=datetime.now(tzutc()) + timedelta(hours=1),
        )

        with pytest.raises(ReservedBatchSessionNotReady):
            validator.validate(snapshot, workload)
