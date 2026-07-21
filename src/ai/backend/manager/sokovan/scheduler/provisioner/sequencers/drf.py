from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal
from typing import override

from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.sokovan import SessionWorkload, SystemSnapshot
from ai.backend.manager.data.sokovan.snapshot import ResourceAllocation

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
    async def sequence(
        self,
        resource_group: str,
        system_snapshot: SystemSnapshot,
        workloads: Sequence[SessionWorkload],
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads based on Dominant Resource Fairness.

        :param resource_group: The resource group (scaling group) name.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to sequence.
        :return: A sequence of SessionWorkload objects sequenced by DRF.
        """
        if not workloads:
            return []

        # Calculate dominant share for each user
        user_dominant_shares: dict[UserID, Decimal] = defaultdict(lambda: Decimal(0))

        # Calculate dominant shares from existing allocations
        for user_id, allocation in system_snapshot.global_scope.occupancy.by_user.items():
            user_dominant_shares[user_id] = self._calculate_dominant_share(
                allocation, system_snapshot.resource_group.total_capacity
            )

        # Sort workloads by dominant share (ascending order - lower share gets higher priority)
        # For users with the same dominant share, maintain original order
        return sorted(workloads, key=lambda w: user_dominant_shares[w.user_uuid])

    def _calculate_dominant_share(
        self, allocation: ResourceAllocation, total_capacity: ResourceSlot
    ) -> Decimal:
        """
        Calculate the dominant share for the given allocation.
        Dominant share is the maximum share across all resource types.
        """
        dominant_share = Decimal(0)

        for slot_name, slot_allocation in allocation.slots.items():
            if slot_name not in total_capacity:
                continue
            capacity = total_capacity[slot_name]
            if capacity == 0:
                continue
            share = slot_allocation.allocated / capacity
            if share > dominant_share:
                dominant_share = share

        return dominant_share
