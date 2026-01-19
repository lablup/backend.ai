from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, override
from uuid import UUID

from ai.backend.manager.data.fair_share import ProjectUserIds
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .sequencer import WorkloadSequencer

if TYPE_CHECKING:
    from ai.backend.manager.repositories.fair_share import FairShareRepository


class FairShareSequencer(WorkloadSequencer):
    """
    A scheduling sequencer that implements Fair Share sequencing.

    This sequencer orders workloads based on fair share factors fetched from the repository.
    Users with higher fair share factors (less historical usage) get higher priority.

    If factors are not available for a user, a default value of 1.0 (highest priority) is used.
    """

    _repository: FairShareRepository

    def __init__(self, repository: FairShareRepository) -> None:
        """Initialize the FairShareSequencer with the repository."""
        self._repository = repository

    @property
    @override
    def name(self) -> str:
        """Return the sequencer name for predicates."""
        return "FairShareSequencer"

    @override
    def success_message(self) -> str:
        """Return a message describing successful sequencing."""
        return "Sessions sequenced using Fair Share algorithm"

    @override
    async def sequence(
        self,
        resource_group: str,
        system_snapshot: SystemSnapshot,
        workloads: Sequence[SessionWorkload],
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads based on Fair Share factors.

        Workloads are sorted by fair_share_factor in descending order.
        Higher fair_share_factor = less historical usage = higher scheduling priority.

        :param resource_group: The resource group (scaling group) name.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to sequence.
        :return: A sequence of SessionWorkload objects ordered by fair share factor.
        """
        if not workloads:
            return []

        # Load fair share factors from repository
        fair_share_factors = await self._load_factors(resource_group, workloads)

        # Sort by fair_share_factor in descending order (higher = more priority)
        # If a user doesn't have a recorded factor, use 1.0 (highest priority for new users)
        return sorted(
            workloads,
            key=lambda w: -fair_share_factors.get(w.user_uuid, Decimal("1.0")),
        )

    async def _load_factors(
        self,
        resource_group: str,
        workloads: Sequence[SessionWorkload],
    ) -> dict[UUID, Decimal]:
        """Load fair share factors from the repository for the given workloads."""
        # Group user_ids by project_id
        project_users: dict[UUID, set[UUID]] = defaultdict(set)
        for w in workloads:
            project_users[w.group_id].add(w.user_uuid)

        # Build ProjectUserIds list
        project_user_ids = [
            ProjectUserIds(project_id=project_id, user_ids=frozenset(user_ids))
            for project_id, user_ids in project_users.items()
        ]

        # Fetch factors from repository
        return await self._repository.get_user_fair_share_factors_batch(
            resource_group, project_user_ids
        )
