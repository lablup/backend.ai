"""Tests for the session dependencies validator."""

from __future__ import annotations

import uuid

import pytest

from ai.backend.common.types import SessionId, SessionResult
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.provisioner.validators.dependencies import (
    DependenciesValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.exceptions import (
    DependenciesNotSatisfied,
)
from ai.backend.manager.views.sokovan.workload import SessionDependencyInfo

from .conftest import SnapshotFactory, WorkloadFactory


def _dep(
    name: str,
    status: SessionStatus,
    result: SessionResult,
) -> SessionDependencyInfo:
    return SessionDependencyInfo(
        depends_on=SessionId(uuid.uuid4()),
        dependency_name=name,
        dependency_status=status,
        dependency_result=result,
    )


class TestDependenciesValidator:
    @pytest.fixture
    def validator(self) -> DependenciesValidator:
        return DependenciesValidator()

    def test_passes_when_no_dependencies(
        self,
        validator: DependenciesValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
    ) -> None:
        workload = workload_factory()
        snapshot = snapshot_factory()

        validator.validate(snapshot, workload)

    def test_passes_when_dependencies_satisfied(
        self,
        validator: DependenciesValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
    ) -> None:
        workload = workload_factory()
        snapshot = snapshot_factory(
            dependencies={
                workload.meta.session_id: [
                    _dep("dep-1", SessionStatus.TERMINATED, SessionResult.SUCCESS),
                    _dep("dep-2", SessionStatus.TERMINATED, SessionResult.SUCCESS),
                ]
            }
        )

        validator.validate(snapshot, workload)

    def test_fails_when_dependency_not_finished(
        self,
        validator: DependenciesValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
    ) -> None:
        workload = workload_factory()
        snapshot = snapshot_factory(
            dependencies={
                workload.meta.session_id: [
                    _dep("dep-running", SessionStatus.RUNNING, SessionResult.UNDEFINED),
                ]
            }
        )

        with pytest.raises(DependenciesNotSatisfied) as exc_info:
            validator.validate(snapshot, workload)
        assert "dep-running" in exc_info.value.summary()

    def test_fails_when_dependency_failed(
        self,
        validator: DependenciesValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
    ) -> None:
        """A terminated-but-failed dependency is not satisfied."""
        workload = workload_factory()
        snapshot = snapshot_factory(
            dependencies={
                workload.meta.session_id: [
                    _dep("dep-failed", SessionStatus.TERMINATED, SessionResult.FAILURE),
                ]
            }
        )

        with pytest.raises(DependenciesNotSatisfied):
            validator.validate(snapshot, workload)

    def test_fails_when_multiple_dependencies_not_satisfied(
        self,
        validator: DependenciesValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
    ) -> None:
        workload = workload_factory()
        snapshot = snapshot_factory(
            dependencies={
                workload.meta.session_id: [
                    _dep("dep-a", SessionStatus.RUNNING, SessionResult.UNDEFINED),
                    _dep("dep-b", SessionStatus.TERMINATED, SessionResult.FAILURE),
                    _dep("dep-ok", SessionStatus.TERMINATED, SessionResult.SUCCESS),
                ]
            }
        )

        with pytest.raises(DependenciesNotSatisfied) as exc_info:
            validator.validate(snapshot, workload)
        summary = exc_info.value.summary()
        assert "dep-a" in summary
        assert "dep-b" in summary
        assert "dep-ok" not in summary
