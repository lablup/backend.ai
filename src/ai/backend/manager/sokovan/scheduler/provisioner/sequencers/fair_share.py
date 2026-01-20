from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING, override
from uuid import UUID

from ai.backend.manager.data.fair_share import ProjectUserIds
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .sequencer import WorkloadSequencer

if TYPE_CHECKING:
    from ai.backend.manager.repositories.fair_share import FairShareRepository

# Default rank for users without a computed rank (placed at lowest priority)
DEFAULT_RANK = sys.maxsize


class FairShareSequencer(WorkloadSequencer):
    """
    A scheduling sequencer that implements Fair Share sequencing.

    This sequencer orders workloads based on scheduling ranks fetched from the repository.
    Users with lower scheduling rank (1 = highest priority) get scheduled first.

    If rank is not available for a user (NULL or not computed), they are placed at lowest priority.
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
        Sequence the workloads based on scheduling ranks.

        Workloads are sorted by scheduling_rank in ascending order.
        Lower rank = higher priority (1 = highest).

        :param resource_group: The resource group (scaling group) name.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to sequence.
        :return: A sequence of SessionWorkload objects ordered by scheduling rank.
        """
        if not workloads:
            return []

        # Load scheduling ranks from repository
        scheduling_ranks = await self._load_ranks(resource_group, workloads)

        # Sort by scheduling_rank in ascending order (lower rank = higher priority)
        # If a user doesn't have a recorded rank, use DEFAULT_RANK (lowest priority)
        return sorted(
            workloads,
            key=lambda w: scheduling_ranks.get(w.user_uuid, DEFAULT_RANK),
        )

    async def _load_ranks(
        self,
        resource_group: str,
        workloads: Sequence[SessionWorkload],
    ) -> dict[UUID, int]:
        """Load scheduling ranks from the repository for the given workloads."""
        # Group user_ids by project_id
        project_users: dict[UUID, set[UUID]] = defaultdict(set)
        for w in workloads:
            project_users[w.group_id].add(w.user_uuid)

        # Build ProjectUserIds list
        project_user_ids = [
            ProjectUserIds(project_id=project_id, user_ids=frozenset(user_ids))
            for project_id, user_ids in project_users.items()
        ]

        # Fetch ranks from repository
        return await self._repository.get_user_scheduling_ranks_batch(
            resource_group, project_user_ids
        )
