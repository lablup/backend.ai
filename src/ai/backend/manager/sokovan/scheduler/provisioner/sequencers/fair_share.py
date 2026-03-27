from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, override
from uuid import UUID

from ai.backend.manager.data.fair_share import ProjectUserIds, UserFairShareFactors
from ai.backend.manager.sokovan.data import SessionWorkload, SystemSnapshot

from .sequencer import WorkloadSequencer

if TYPE_CHECKING:
    from ai.backend.manager.repositories.fair_share import FairShareRepository

# Default factor for users without computed factors (lowest priority)
# Factor 0 means no entitlement (maximum usage)
DEFAULT_FACTOR = Decimal("0")


class FairShareSequencer(WorkloadSequencer):
    """
    A scheduling sequencer that implements Fair Share sequencing.

    This sequencer orders workloads based on fair share factors fetched from the repository
    using a 3-way JOIN across domain, project, and user fair share tables.

    Sorting priority (descending - higher factor = higher priority):
    1. Domain fair share factor
    2. Project fair share factor
    3. User fair share factor

    Users with higher factors (lower historical usage) get scheduled first.
    If factors are not available for a user, they are placed at lowest priority.
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
        Sequence the workloads based on fair share factors.

        Workloads are sorted by (domain_factor, project_factor, user_factor) in descending order.
        Higher factor = higher priority (users with lower historical usage get scheduled first).

        :param resource_group: The resource group (scaling group) name.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to sequence.
        :return: A sequence of SessionWorkload objects ordered by fair share factors.
        """
        if not workloads:
            return []

        # Load fair share factors from repository using 3-way JOIN
        user_factors = await self._load_factors(resource_group, workloads)

        # Sort by factors in descending order (higher factor = higher priority)
        # If a user doesn't have recorded factors, use default (lowest priority)
        return sorted(
            workloads,
            key=lambda w: self._get_sort_key(w.user_uuid, user_factors),
        )

    async def _load_factors(
        self,
        resource_group: str,
        workloads: Sequence[SessionWorkload],
    ) -> dict[UUID, UserFairShareFactors]:
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

        # Fetch factors from repository using 3-way JOIN
        return await self._repository.get_user_fair_share_factors_batch(
            resource_group, project_user_ids
        )

    def _get_sort_key(
        self,
        user_uuid: UUID,
        user_factors: dict[UUID, UserFairShareFactors],
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Get the sort key for a workload based on its user's factors.

        Returns negated factors for descending sort (higher factor = higher priority).
        """
        factors = user_factors.get(user_uuid)
        if factors is None:
            # No factors recorded - lowest priority
            return (-DEFAULT_FACTOR, -DEFAULT_FACTOR, -DEFAULT_FACTOR)
        return factors.sort_key()
