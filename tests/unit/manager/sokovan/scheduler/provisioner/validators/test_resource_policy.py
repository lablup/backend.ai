"""Tests for the consolidated resource policy validator.

ResourcePolicyValidator covers what used to be separate validators: user,
project, and domain slot quotas plus the user's concurrent-session caps.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

import pytest

from ai.backend.common.types import SessionTypes
from ai.backend.manager.sokovan.scheduler.provisioner.validators.exceptions import (
    ConcurrencyLimitExceeded,
    DomainResourceQuotaExceeded,
    MultipleValidationErrors,
    ProjectResourceQuotaExceeded,
    UserResourceQuotaExceeded,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.resource_policy import (
    ResourcePolicyValidator,
)
from ai.backend.manager.views.sokovan.snapshot import (
    ResourceLimit,
    ResourceOccupancySnapshot,
    UserResourceLimit,
)

from .conftest import SnapshotFactory, WorkloadFactory, slot_map

OccupancyFactory = Callable[..., ResourceOccupancySnapshot]


def _user_limit(
    slots: Mapping[str, str],
    *,
    max_session_count: int | None = None,
    max_sftp_session_count: int | None = None,
) -> UserResourceLimit:
    return UserResourceLimit(
        slots=slot_map(slots),
        max_session_count=max_session_count,
        max_sftp_session_count=max_sftp_session_count,
    )


@pytest.fixture
def validator() -> ResourcePolicyValidator:
    return ResourcePolicyValidator()


class TestUserSlotQuota:
    def test_passes_when_under_limit(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "2", "mem": "4096"})
        snapshot = snapshot_factory(
            user_limit=_user_limit({"cpu": "10", "mem": "20480"}),
            occupancy=occupancy_factory(user_slots={"cpu": ("2", "0"), "mem": ("4096", "0")}),
        )

        validator.validate(snapshot, workload)

    def test_fails_when_exceeds_limit(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "4", "mem": "8192"})
        snapshot = snapshot_factory(
            user_limit=_user_limit({"cpu": "10", "mem": "20480"}),
            occupancy=occupancy_factory(user_slots={"cpu": ("4", "3"), "mem": ("8192", "0")}),
        )

        # allocated cpu = 4 + 3 = 7; 7 + 4 > 10
        with pytest.raises(UserResourceQuotaExceeded):
            validator.validate(snapshot, workload)

    def test_passes_when_no_policy(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
    ) -> None:
        """A missing user limit means the scope imposes no quota."""
        workload = workload_factory(slots={"cpu": "1000", "mem": "999999"})
        snapshot = snapshot_factory()

        validator.validate(snapshot, workload)

    def test_passes_when_no_current_occupancy(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "2", "mem": "4096"})
        snapshot = snapshot_factory(user_limit=_user_limit({"cpu": "10", "mem": "20480"}))

        validator.validate(snapshot, workload)


class TestConcurrencyLimits:
    def test_passes_when_under_limit(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        workload = workload_factory()
        snapshot = snapshot_factory(
            user_limit=_user_limit({"cpu": "100", "mem": "999999"}, max_session_count=5),
            occupancy=occupancy_factory(session_count=3),
        )

        validator.validate(snapshot, workload)

    def test_fails_when_at_limit(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        workload = workload_factory()
        snapshot = snapshot_factory(
            user_limit=_user_limit({"cpu": "100", "mem": "999999"}, max_session_count=3),
            occupancy=occupancy_factory(session_count=3),
        )

        with pytest.raises(ConcurrencyLimitExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "3 concurrent" in exc_info.value.summary()

    def test_private_session_checks_sftp_count(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        """Private (SYSTEM) sessions count against the SFTP cap only."""
        workload = workload_factory(session_type=SessionTypes.SYSTEM)
        snapshot = snapshot_factory(
            user_limit=_user_limit(
                {"cpu": "100", "mem": "999999"},
                max_session_count=1,
                max_sftp_session_count=2,
            ),
            # session_count is already at its cap, but that cap is irrelevant
            occupancy=occupancy_factory(session_count=1, sftp_session_count=2),
        )

        with pytest.raises(ConcurrencyLimitExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "SFTP" in exc_info.value.summary()

    def test_private_session_passes_under_sftp_limit(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        workload = workload_factory(session_type=SessionTypes.SYSTEM)
        snapshot = snapshot_factory(
            user_limit=_user_limit(
                {"cpu": "100", "mem": "999999"},
                max_session_count=1,
                max_sftp_session_count=5,
            ),
            occupancy=occupancy_factory(session_count=1, sftp_session_count=2),
        )

        validator.validate(snapshot, workload)

    def test_passes_when_limit_is_none(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        """A None cap means unlimited sessions."""
        workload = workload_factory()
        snapshot = snapshot_factory(
            user_limit=_user_limit({"cpu": "100", "mem": "999999"}, max_session_count=None),
            occupancy=occupancy_factory(session_count=1000),
        )

        validator.validate(snapshot, workload)

    def test_zero_limit_blocks_all_sessions(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
    ) -> None:
        """A zero cap admits no session of that kind."""
        workload = workload_factory()
        snapshot = snapshot_factory(
            user_limit=_user_limit({"cpu": "100", "mem": "999999"}, max_session_count=0),
        )

        with pytest.raises(ConcurrencyLimitExceeded):
            validator.validate(snapshot, workload)


class TestProjectSlotQuota:
    def test_fails_when_exceeds_limit(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "4", "mem": "8192"})
        snapshot = snapshot_factory(
            project_limit=ResourceLimit(slots=slot_map({"cpu": "10", "mem": "999999"})),
            occupancy=occupancy_factory(project_slots={"cpu": ("7", "0")}),
        )

        with pytest.raises(ProjectResourceQuotaExceeded):
            validator.validate(snapshot, workload)

    def test_passes_when_under_limit(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "2", "mem": "4096"})
        snapshot = snapshot_factory(
            project_limit=ResourceLimit(slots=slot_map({"cpu": "10", "mem": "999999"})),
            occupancy=occupancy_factory(project_slots={"cpu": ("7", "0")}),
        )

        validator.validate(snapshot, workload)


class TestDomainSlotQuota:
    def test_fails_when_exceeds_limit(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "4", "mem": "8192"})
        snapshot = snapshot_factory(
            domain_limit=ResourceLimit(slots=slot_map({"cpu": "10", "mem": "999999"})),
            occupancy=occupancy_factory(domain_slots={"cpu": ("3", "4")}),
        )

        with pytest.raises(DomainResourceQuotaExceeded):
            validator.validate(snapshot, workload)

    def test_passes_when_under_limit(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "2", "mem": "4096"})
        snapshot = snapshot_factory(
            domain_limit=ResourceLimit(slots=slot_map({"cpu": "10", "mem": "999999"})),
            occupancy=occupancy_factory(domain_slots={"cpu": ("3", "4")}),
        )

        validator.validate(snapshot, workload)


class TestMultipleViolations:
    def test_all_violated_scopes_are_reported(
        self,
        validator: ResourcePolicyValidator,
        workload_factory: WorkloadFactory,
        snapshot_factory: SnapshotFactory,
        occupancy_factory: OccupancyFactory,
    ) -> None:
        """Every violated quota is collected, not just the first one."""
        workload = workload_factory(slots={"cpu": "100", "mem": "4096"})
        snapshot = snapshot_factory(
            user_limit=_user_limit({"cpu": "10", "mem": "999999"}),
            project_limit=ResourceLimit(slots=slot_map({"cpu": "10", "mem": "999999"})),
            domain_limit=ResourceLimit(slots=slot_map({"cpu": "10", "mem": "999999"})),
            occupancy=occupancy_factory(),
        )

        with pytest.raises(MultipleValidationErrors) as exc_info:
            validator.validate(snapshot, workload)
        summary = exc_info.value.summary()
        assert "UserResourceQuotaExceeded" in summary
        assert "ProjectResourceQuotaExceeded" in summary
        assert "DomainResourceQuotaExceeded" in summary
