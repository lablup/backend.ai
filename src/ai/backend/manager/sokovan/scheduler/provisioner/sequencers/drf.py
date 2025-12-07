from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal
from typing import override

from ai.backend.common.types import AccessKey, ResourceSlot

from ..types import SessionWorkload, SystemSnapshot
from .sequencer import WorkloadSequencer


class DRFSequencer(WorkloadSequencer):
    """
    A scheduling sequencer that implements Dominant Resource Fairness (DRF) sequencing.
    This sequencer will sequence workloads based on their resource usage and fairness.
    """

    @property
    @override
    def name(self) -> str:
        """
        Return the sequencer name for predicates.
        """
        return "DRFSequencer"

    @override
    def success_message(self) -> str:
        """
        Return a message describing successful sequencing.
        """
        return "Sessions sequenced using Dominant Resource Fairness algorithm"

    @override
    def sequence(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads based on Dominant Resource Fairness.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to sequence.
        :return: A sequence of SessionWorkload objects sequenced by DRF.
        """
        if not workloads:
            return []

        # Calculate dominant share for each user
        user_dominant_shares: dict[AccessKey, Decimal] = defaultdict(lambda: Decimal(0))

        # Calculate dominant shares from existing allocations
        for access_key, occupancy in system_snapshot.resource_occupancy.by_keypair.items():
            dominant_share = self._calculate_dominant_share(
                occupancy.occupied_slots, system_snapshot.total_capacity
            )
            user_dominant_shares[access_key] = dominant_share

        # Sort workloads by dominant share (ascending order - lower share gets higher priority)
        # For users with the same dominant share, maintain original order
        sorted_workloads = sorted(workloads, key=lambda w: user_dominant_shares[w.access_key])
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
