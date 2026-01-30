"""Tests for FairShareAggregator slice generation logic.

Verifies that slices are correctly aligned to 5-minute clock boundaries
and that partial slices are only allowed at kernel start and termination.

Since FairShareAggregator is now pure computation (no repositories),
tests can be written without mocks.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.fair_share.aggregator import (
    SLICE_DURATION_SECONDS,
    FairShareAggregator,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.resource_usage_history import (
        KernelUsageRecordCreatorSpec,
    )


def make_datetime(hour: int, minute: int, second: int = 0) -> datetime:
    """Create a datetime with fixed date for testing."""
    return datetime(2024, 1, 15, hour, minute, second, tzinfo=UTC)


@pytest.fixture
def mock_kernel_info() -> MagicMock:
    """Create a mock KernelInfo with required fields."""
    kernel = MagicMock()
    kernel.id = uuid4()
    kernel.session.session_id = str(uuid4())
    kernel.user_permission.user_uuid = uuid4()
    kernel.user_permission.group_id = uuid4()
    kernel.user_permission.domain_name = "default"
    kernel.resource.occupied_slots = ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")})
    kernel.lifecycle.starts_at = None
    kernel.lifecycle.last_observed_at = None
    kernel.lifecycle.terminated_at = None
    return kernel


@pytest.fixture
def aggregator() -> FairShareAggregator:
    """Create FairShareAggregator - no mocks needed (pure computation)."""
    return FairShareAggregator()


class TestFloorToBoundary:
    """Tests for _floor_to_boundary method."""

    def test_floor_non_boundary_time(self, aggregator: FairShareAggregator) -> None:
        """Non-boundary times should be floored to previous boundary."""
        assert aggregator._floor_to_boundary(make_datetime(7, 47, 30)) == make_datetime(7, 45, 0)
        assert aggregator._floor_to_boundary(make_datetime(7, 52, 15)) == make_datetime(7, 50, 0)
        assert aggregator._floor_to_boundary(make_datetime(7, 44, 59)) == make_datetime(7, 40, 0)

    def test_floor_exact_boundary(self, aggregator: FairShareAggregator) -> None:
        """Exact boundary times should remain unchanged."""
        assert aggregator._floor_to_boundary(make_datetime(7, 45, 0)) == make_datetime(7, 45, 0)
        assert aggregator._floor_to_boundary(make_datetime(7, 50, 0)) == make_datetime(7, 50, 0)
        assert aggregator._floor_to_boundary(make_datetime(8, 0, 0)) == make_datetime(8, 0, 0)


class TestPrepareKernelUsageSpecs:
    """Tests for _prepare_kernel_usage_specs method."""

    def test_first_observation_partial_start_allowed(
        self,
        aggregator: FairShareAggregator,
        mock_kernel_info: MagicMock,
    ) -> None:
        """First observation allows partial start slice from starts_at."""
        mock_kernel_info.lifecycle.starts_at = make_datetime(7, 42, 30)
        mock_kernel_info.lifecycle.last_observed_at = None  # First observation
        mock_kernel_info.lifecycle.terminated_at = None  # RUNNING

        specs, last_observed_at = aggregator._prepare_kernel_usage_specs(
            mock_kernel_info, "default", now=make_datetime(7, 47, 0)
        )

        # Only one slice: 07:42:30 -> 07:45:00 (partial start)
        # 07:45:00 -> 07:47:00 is NOT generated (now floored to 07:45:00)
        assert len(specs) == 1
        assert specs[0].period_start == make_datetime(7, 42, 30)
        assert specs[0].period_end == make_datetime(7, 45, 0)
        assert last_observed_at == make_datetime(7, 45, 0)  # floored boundary

    def test_running_kernel_only_complete_slices(
        self,
        aggregator: FairShareAggregator,
        mock_kernel_info: MagicMock,
    ) -> None:
        """RUNNING kernel should only generate complete slices up to last boundary."""
        mock_kernel_info.lifecycle.starts_at = make_datetime(7, 40, 0)
        mock_kernel_info.lifecycle.last_observed_at = make_datetime(7, 45, 0)  # Previous boundary
        mock_kernel_info.lifecycle.terminated_at = None  # RUNNING

        # now = 07:52:30 -> floors to 07:50:00
        specs, last_observed_at = aggregator._prepare_kernel_usage_specs(
            mock_kernel_info, "default", now=make_datetime(7, 52, 30)
        )

        # One complete slice: 07:45:00 -> 07:50:00
        # 07:50:00 -> 07:52:30 is NOT generated
        assert len(specs) == 1
        assert specs[0].period_start == make_datetime(7, 45, 0)
        assert specs[0].period_end == make_datetime(7, 50, 0)
        assert last_observed_at == make_datetime(7, 50, 0)

    def test_running_kernel_no_slices_before_boundary(
        self,
        aggregator: FairShareAggregator,
        mock_kernel_info: MagicMock,
    ) -> None:
        """RUNNING kernel should generate no slices if next boundary not reached."""
        mock_kernel_info.lifecycle.starts_at = make_datetime(7, 40, 0)
        mock_kernel_info.lifecycle.last_observed_at = make_datetime(7, 45, 0)
        mock_kernel_info.lifecycle.terminated_at = None  # RUNNING

        # now = 07:48:00 -> floors to 07:45:00, same as last_observed_at
        specs, last_observed_at = aggregator._prepare_kernel_usage_specs(
            mock_kernel_info, "default", now=make_datetime(7, 48, 0)
        )

        # No slices: floored now (07:45:00) <= last_observed_at (07:45:00)
        assert len(specs) == 0
        assert last_observed_at == make_datetime(7, 45, 0)

    def test_terminated_kernel_partial_end_allowed(
        self,
        aggregator: FairShareAggregator,
        mock_kernel_info: MagicMock,
    ) -> None:
        """TERMINATED kernel allows partial end slice at terminated_at."""
        mock_kernel_info.lifecycle.starts_at = make_datetime(7, 40, 0)
        mock_kernel_info.lifecycle.last_observed_at = make_datetime(7, 50, 0)
        mock_kernel_info.lifecycle.terminated_at = make_datetime(7, 53, 30)  # TERMINATED

        specs, last_observed_at = aggregator._prepare_kernel_usage_specs(
            mock_kernel_info, "default", now=make_datetime(7, 55, 0)
        )

        # One partial slice: 07:50:00 -> 07:53:30
        assert len(specs) == 1
        assert specs[0].period_start == make_datetime(7, 50, 0)
        assert specs[0].period_end == make_datetime(7, 53, 30)
        assert last_observed_at == make_datetime(7, 53, 30)


class TestPrepareKernelUsageRecords:
    """Tests for prepare_kernel_usage_records public method."""

    def test_processes_multiple_kernels(
        self,
        aggregator: FairShareAggregator,
    ) -> None:
        """Test processing multiple kernels at once."""
        # Create two mock kernels
        kernel1 = MagicMock()
        kernel1.id = uuid4()
        kernel1.session.session_id = str(uuid4())
        kernel1.user_permission.user_uuid = uuid4()
        kernel1.user_permission.group_id = uuid4()
        kernel1.user_permission.domain_name = "default"
        kernel1.resource.occupied_slots = ResourceSlot({"cpu": Decimal("2")})
        kernel1.lifecycle.starts_at = make_datetime(7, 40, 0)
        kernel1.lifecycle.last_observed_at = make_datetime(7, 45, 0)
        kernel1.lifecycle.terminated_at = None

        kernel2 = MagicMock()
        kernel2.id = uuid4()
        kernel2.session.session_id = str(uuid4())
        kernel2.user_permission.user_uuid = uuid4()
        kernel2.user_permission.group_id = uuid4()
        kernel2.user_permission.domain_name = "default"
        kernel2.resource.occupied_slots = ResourceSlot({"cpu": Decimal("4")})
        kernel2.lifecycle.starts_at = make_datetime(7, 42, 0)
        kernel2.lifecycle.last_observed_at = make_datetime(7, 45, 0)
        kernel2.lifecycle.terminated_at = None

        result = aggregator.prepare_kernel_usage_records(
            kernels=[kernel1, kernel2],
            scaling_group="default",
            now=make_datetime(7, 52, 0),
        )

        # Both kernels should have one slice: 07:45:00 -> 07:50:00
        assert result.observed_count == 2
        assert len(result.specs) == 2
        assert len(result.kernel_observation_times) == 2


class TestScenarioConsecutiveObservations:
    """
    Scenario tests for consecutive observations.

    Kernel starts at 07:42:30

    1st observation (now = 07:47:00):
      - 07:42:30 -> 07:45:00 generated (partial start, OK)
      - last_observed_at = 07:45:00

    2nd observation (now = 07:48:00):
      - No slices (07:48:00 floors to 07:45:00, same as last_observed_at)
      - last_observed_at = 07:45:00 (unchanged)

    3rd observation (now = 07:52:00):
      - 07:45:00 -> 07:50:00 generated (full 5min)
      - last_observed_at = 07:50:00

    4th observation - kernel terminates (terminated_at = 07:53:30):
      - 07:50:00 -> 07:53:30 generated (partial end, OK)
      - last_observed_at = 07:53:30
    """

    def test_scenario_full_lifecycle(
        self,
        aggregator: FairShareAggregator,
        mock_kernel_info: MagicMock,
    ) -> None:
        """Test full kernel lifecycle with consecutive observations."""
        all_specs: list[KernelUsageRecordCreatorSpec] = []
        mock_kernel_info.lifecycle.starts_at = make_datetime(7, 42, 30)

        # 1st observation: now = 07:47:00
        mock_kernel_info.lifecycle.last_observed_at = None
        mock_kernel_info.lifecycle.terminated_at = None
        specs_1, last_obs_1 = aggregator._prepare_kernel_usage_specs(
            mock_kernel_info, "default", now=make_datetime(7, 47, 0)
        )
        all_specs.extend(specs_1)

        assert len(specs_1) == 1
        assert specs_1[0].period_start == make_datetime(7, 42, 30)
        assert specs_1[0].period_end == make_datetime(7, 45, 0)
        assert last_obs_1 == make_datetime(7, 45, 0)

        # 2nd observation: now = 07:48:00 (before next boundary)
        mock_kernel_info.lifecycle.last_observed_at = last_obs_1
        specs_2, last_obs_2 = aggregator._prepare_kernel_usage_specs(
            mock_kernel_info, "default", now=make_datetime(7, 48, 0)
        )
        all_specs.extend(specs_2)

        assert len(specs_2) == 0  # No slices generated
        assert last_obs_2 == make_datetime(7, 45, 0)  # Unchanged

        # 3rd observation: now = 07:52:00 (after next boundary)
        mock_kernel_info.lifecycle.last_observed_at = last_obs_2
        specs_3, last_obs_3 = aggregator._prepare_kernel_usage_specs(
            mock_kernel_info, "default", now=make_datetime(7, 52, 0)
        )
        all_specs.extend(specs_3)

        assert len(specs_3) == 1
        assert specs_3[0].period_start == make_datetime(7, 45, 0)
        assert specs_3[0].period_end == make_datetime(7, 50, 0)
        assert last_obs_3 == make_datetime(7, 50, 0)

        # 4th observation: kernel terminates at 07:53:30
        mock_kernel_info.lifecycle.last_observed_at = last_obs_3
        mock_kernel_info.lifecycle.terminated_at = make_datetime(7, 53, 30)
        specs_4, last_obs_4 = aggregator._prepare_kernel_usage_specs(
            mock_kernel_info, "default", now=make_datetime(7, 55, 0)
        )
        all_specs.extend(specs_4)

        assert len(specs_4) == 1
        assert specs_4[0].period_start == make_datetime(7, 50, 0)
        assert specs_4[0].period_end == make_datetime(7, 53, 30)
        assert last_obs_4 == make_datetime(7, 53, 30)

        # Verify all slices are continuous
        assert len(all_specs) == 3
        for i in range(len(all_specs) - 1):
            assert all_specs[i].period_end == all_specs[i + 1].period_start, (
                f"Gap detected between slice {i} and {i + 1}"
            )

        # Total coverage: 07:42:30 -> 07:53:30 (11 minutes)
        assert all_specs[0].period_start == make_datetime(7, 42, 30)
        assert all_specs[-1].period_end == make_datetime(7, 53, 30)


class TestSliceGeneration:
    """Tests for _generate_slice_specs method."""

    def test_multiple_complete_slices(
        self,
        aggregator: FairShareAggregator,
        mock_kernel_info: MagicMock,
    ) -> None:
        """Test generation of multiple complete 5-minute slices."""
        specs = aggregator._generate_slice_specs(
            mock_kernel_info,
            "default",
            start_time=make_datetime(7, 45, 0),
            end_time=make_datetime(8, 0, 0),
        )

        # Three complete slices
        assert len(specs) == 3
        assert specs[0].period_start == make_datetime(7, 45, 0)
        assert specs[0].period_end == make_datetime(7, 50, 0)
        assert specs[1].period_start == make_datetime(7, 50, 0)
        assert specs[1].period_end == make_datetime(7, 55, 0)
        assert specs[2].period_start == make_datetime(7, 55, 0)
        assert specs[2].period_end == make_datetime(8, 0, 0)

    def test_resource_seconds_calculation(
        self,
        aggregator: FairShareAggregator,
        mock_kernel_info: MagicMock,
    ) -> None:
        """Verify resource-seconds are calculated correctly."""
        # 2.5 minute slice with cpu=2, mem=4096
        specs = aggregator._generate_slice_specs(
            mock_kernel_info,
            "default",
            start_time=make_datetime(7, 42, 30),
            end_time=make_datetime(7, 45, 0),
        )

        assert len(specs) == 1
        # 2.5 minutes = 150 seconds
        # cpu: 2 * 150 = 300, mem: 4096 * 150 = 614400
        assert specs[0].resource_usage["cpu"] == Decimal("300")
        assert specs[0].resource_usage["mem"] == Decimal("614400")

    def test_empty_range_returns_no_slices(
        self,
        aggregator: FairShareAggregator,
        mock_kernel_info: MagicMock,
    ) -> None:
        """Verify no slices when start_time >= end_time."""
        same_time = make_datetime(7, 45, 0)
        specs = aggregator._generate_slice_specs(
            mock_kernel_info,
            "default",
            same_time,
            same_time,
        )
        assert len(specs) == 0

    def test_slice_duration_constant(self) -> None:
        """Verify SLICE_DURATION_SECONDS is 300 (5 minutes)."""
        assert SLICE_DURATION_SECONDS == 300
