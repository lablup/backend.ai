from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal
from typing import override

from ai.backend.common.types import AccessKey, ResourceSlot

from ..prioritizers.prioritizer import SchedulingPrioritizer
from ..types import SessionWorkload, SystemSnapshot


class DRFSchedulingPrioritizer(SchedulingPrioritizer):
    """
    A scheduling prioritizer that implements Dominant Resource Fairness (DRF) prioritization.
    This prioritizer will prioritize workloads based on their resource usage and fairness.
    """

    @property
    @override
    def name(self) -> str:
        """
        The name of the prioritizer.
        This should be overridden by subclasses to provide a unique identifier.
        """
        return "DRF-scheduling-prioritizer"

    @override
    async def prioritize(
        self, system_snapshot: SystemSnapshot, workload: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """
        Prioritize the workloads based on Dominant Resource Fairness.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workload: A sequence of SessionWorkload objects to prioritize.
        :return: A sequence of SessionWorkload objects prioritized by DRF.
        """
        if not workload:
            return []

        # Calculate dominant share for each user
        user_dominant_shares: dict[AccessKey, Decimal] = defaultdict(lambda: Decimal(0))

        # Calculate dominant shares from existing allocations
        for access_key, occupied_slots in system_snapshot.user_allocations.items():
            dominant_share = self._calculate_dominant_share(
                occupied_slots, system_snapshot.total_capacity
            )
            user_dominant_shares[access_key] = dominant_share

        # Sort workloads by dominant share (ascending order - lower share gets higher priority)
        # For users with the same dominant share, maintain original order
        sorted_workloads = sorted(workload, key=lambda w: user_dominant_shares[w.access_key])

        return sorted_workloads

    def _calculate_dominant_share(
        self, resource_slots: ResourceSlot, total_capacity: ResourceSlot
    ) -> Decimal:
        """
        Calculate the dominant share for given resource slots.
        Dominant share is the maximum share across all resource types.
        """
        dominant_share = Decimal(0)

        # Ensure keys are synchronized
        total_capacity.sync_keys(resource_slots)

        for slot, value in resource_slots.items():
            capacity = Decimal(total_capacity[slot])
            if capacity == 0:
                continue
            share = Decimal(value) / capacity
            if share > dominant_share:
                dominant_share = share

        return dominant_share
