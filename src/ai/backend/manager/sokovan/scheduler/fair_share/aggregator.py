"""Fair share aggregator for computing kernel resource usage.

This module provides the FairShareAggregator that performs pure computation:
1. Prepares kernel usage records (resource-seconds) in 5-minute slices
2. Aggregates usage by user/project/domain (future)
3. Calculates scheduling ranks for fair share sequencing (future)

The aggregator is stateless and does not interact with databases directly.
Repository operations are handled by FairShareObserver.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.repositories.resource_usage_history import (
    KernelUsageRecordCreatorSpec,
)

# Observation slice duration (5 minutes)
SLICE_DURATION_SECONDS = 300

if TYPE_CHECKING:
    from ai.backend.manager.data.kernel.types import KernelInfo


@dataclass
class KernelUsagePreparationResult:
    """Result of preparing kernel usage records.

    Attributes:
        specs: List of kernel usage record specs for bulk creation
        kernel_observation_times: Mapping of kernel_id to last_observed_at timestamp
        observed_count: Number of kernels with generated specs
    """

    specs: list[KernelUsageRecordCreatorSpec] = field(default_factory=list)
    kernel_observation_times: dict[UUID, datetime] = field(default_factory=dict)
    observed_count: int = 0


class FairShareAggregator:
    """Computes kernel usage for fair share scheduling.

    This class performs pure computation without database interactions.
    It prepares kernel usage records aligned to 5-minute clock boundaries.

    Partial slices are only allowed at:
    - Start: When starts_at is not on a boundary (first observation only)
    - End: When the kernel terminates at a non-boundary time

    For RUNNING kernels, only complete slices up to the last boundary are generated.
    """

    def prepare_kernel_usage_records(
        self,
        kernels: Sequence[KernelInfo],
        scaling_group: str,
        now: datetime,
    ) -> KernelUsagePreparationResult:
        """Prepare kernel usage records for bulk creation.

        For each kernel:
        1. Determine period: last_observed_at (or starts_at) to end_time
           - RUNNING kernels: end_time = floor(now) to last boundary
           - TERMINATED kernels: end_time = terminated_at
        2. Split period into 5-minute slices aligned to clock boundaries
        3. Create usage record specs for each slice

        Args:
            kernels: Kernels to process
            scaling_group: The scaling group name
            now: Current time from DB

        Returns:
            KernelUsagePreparationResult containing specs and metadata
        """
        result = KernelUsagePreparationResult()

        for kernel in kernels:
            kernel_specs, observation_end = self._prepare_kernel_usage_specs(
                kernel, scaling_group, now
            )
            if kernel_specs:
                result.specs.extend(kernel_specs)
                result.kernel_observation_times[UUID(str(kernel.id))] = observation_end
                result.observed_count += 1

        return result

    def _prepare_kernel_usage_specs(
        self,
        kernel: KernelInfo,
        scaling_group: str,
        now: datetime,
    ) -> tuple[list[KernelUsageRecordCreatorSpec], datetime]:
        """Prepare usage record specs for a single kernel.

        Generates 5-minute slices aligned to clock boundaries.
        Partial slices are only allowed at:
        - Start: When starts_at is not on a boundary (first observation only)
        - End: When the kernel terminates at a non-boundary time

        For RUNNING kernels, only complete slices up to the last boundary are generated.

        Args:
            kernel: Kernel to process
            scaling_group: The scaling group
            now: Current time from DB

        Returns:
            Tuple of (list of specs, last_observed_at to save)
        """
        is_first_observation = kernel.lifecycle.last_observed_at is None
        is_terminated = kernel.lifecycle.terminated_at is not None

        # Determine start time
        start_time: datetime
        if is_first_observation:
            if kernel.lifecycle.starts_at is None:
                raise ValueError(f"Kernel {kernel.id} has no starts_at for first observation")
            start_time = kernel.lifecycle.starts_at
        else:
            assert kernel.lifecycle.last_observed_at is not None  # for type narrowing
            start_time = kernel.lifecycle.last_observed_at

        # Determine end time based on kernel status
        end_time: datetime
        if is_terminated:
            # TERMINATED: use terminated_at (allows partial end slice)
            assert kernel.lifecycle.terminated_at is not None  # for type narrowing
            end_time = kernel.lifecycle.terminated_at
        else:
            # RUNNING: floor to last complete boundary (no partial end slice)
            end_time = self._floor_to_boundary(now)

        # Validate time range
        if end_time <= start_time:
            # Not enough time has passed to generate any slices
            return [], start_time

        # Generate 5-minute slices
        specs = self._generate_slice_specs(
            kernel=kernel,
            scaling_group=scaling_group,
            start_time=start_time,
            end_time=end_time,
        )

        # Return end_time as the new last_observed_at
        # For RUNNING: this is floored to boundary
        # For TERMINATED: this is terminated_at
        return specs, end_time

    def _generate_slice_specs(
        self,
        kernel: KernelInfo,
        scaling_group: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[KernelUsageRecordCreatorSpec]:
        """Generate 5-minute slice specs aligned to clock boundaries.

        Slices are aligned to 5-minute clock boundaries (00:00, 00:05, 00:10, etc.).
        The caller is responsible for adjusting start_time and end_time to control
        whether partial slices are allowed.

        Args:
            kernel: Kernel info
            scaling_group: The scaling group
            start_time: Start of observation period
            end_time: End of observation period

        Returns:
            List of usage record specs for each slice
        """
        specs: list[KernelUsageRecordCreatorSpec] = []

        current_start = start_time
        while current_start < end_time:
            # Calculate next 5-minute boundary after current_start
            start_epoch = int(current_start.timestamp())
            next_boundary_epoch = (
                (start_epoch // SLICE_DURATION_SECONDS) + 1
            ) * SLICE_DURATION_SECONDS
            next_boundary = datetime.fromtimestamp(next_boundary_epoch, tz=current_start.tzinfo)

            # Slice ends at the next boundary or end_time, whichever is earlier
            current_end = min(next_boundary, end_time)
            slice_seconds = (current_end - current_start).total_seconds()

            if slice_seconds <= 0:
                break

            # Calculate resource-seconds for this slice
            resource_seconds = self._calculate_resource_seconds(
                kernel.resource.occupied_slots,
                slice_seconds,
            )

            spec = KernelUsageRecordCreatorSpec(
                kernel_id=UUID(str(kernel.id)),
                session_id=UUID(kernel.session.session_id),
                user_uuid=kernel.user_permission.user_uuid,
                project_id=kernel.user_permission.group_id,
                domain_name=kernel.user_permission.domain_name,
                resource_group=scaling_group,
                period_start=current_start,
                period_end=current_end,
                resource_usage=resource_seconds,
            )
            specs.append(spec)

            current_start = current_end

        return specs

    def _floor_to_boundary(self, dt: datetime) -> datetime:
        """Floor datetime to the previous 5-minute boundary.

        Examples:
            07:47:30 -> 07:45:00
            07:50:00 -> 07:50:00 (already on boundary)
            07:52:15 -> 07:50:00

        Args:
            dt: Datetime to floor

        Returns:
            Datetime floored to 5-minute boundary
        """
        epoch = int(dt.timestamp())
        floored_epoch = (epoch // SLICE_DURATION_SECONDS) * SLICE_DURATION_SECONDS
        return datetime.fromtimestamp(floored_epoch, tz=dt.tzinfo)

    def _calculate_resource_seconds(
        self,
        slots: ResourceSlot,
        seconds: float,
    ) -> ResourceSlot:
        """Convert resource slots to resource-seconds.

        Multiplies each resource value by the number of seconds to get
        the total resource-seconds consumed during the period.

        Args:
            slots: Resource slots (e.g., {"cpu": 2, "mem": 4096})
            seconds: Duration in seconds

        Returns:
            ResourceSlot with values in resource-seconds
        """
        return ResourceSlot({key: value * Decimal(str(seconds)) for key, value in slots.items()})
