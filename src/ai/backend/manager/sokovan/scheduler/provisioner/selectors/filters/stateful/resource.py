"""Stateful filter: agents must have the requested slots remaining."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, override

from ai.backend.manager.sokovan.scheduler.provisioner.selectors.filters.stateful.filter import (
    AbstractStatefulTrackerFilter,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.agent import AgentLimit

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
        AgentSelectionCriteria,
    )


class ResourceTrackerFilter(AbstractStatefulTrackerFilter):
    """Keeps agents whose remaining slots cover the requested slots."""

    @override
    def name(self) -> str:
        return "resource"

    @override
    def success_message(self) -> str:
        return "Agents with sufficient resources found"

    @override
    def filter(
        self,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
        limit: AgentLimit,
    ) -> Sequence[AgentStateTracker]:
        return [tracker for tracker in trackers if self._has_room(tracker, resource_req)]

    def _has_room(
        self,
        tracker: AgentStateTracker,
        resource_req: ResourceRequirements,
    ) -> bool:
        remaining = tracker.remaining_slots()
        return all(
            requested <= remaining.get(slot_name, Decimal(0))
            for slot_name, requested in resource_req.requested_slots.slots.items()
        )
