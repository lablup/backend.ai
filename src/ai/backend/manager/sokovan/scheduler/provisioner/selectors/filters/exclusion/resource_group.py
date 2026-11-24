"""Exclusion filter: agents must belong to the requirement's resource group."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, override

from ai.backend.manager.sokovan.scheduler.provisioner.selectors.filters.exclusion.filter import (
    AbstractExclusionTrackerFilter,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
        AgentSelectionCriteria,
    )


class ResourceGroupTrackerFilter(AbstractExclusionTrackerFilter):
    """Keeps only agents of the requirement's resource group."""

    @override
    def name(self) -> str:
        return "resource-group"

    @override
    def success_message(self) -> str:
        return "Agents in the resource group found"

    @override
    def failure_message(
        self,
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
    ) -> str:
        return f"no agent is available in resource group '{resource_req.resource_group_id}'"

    @override
    def filter(
        self,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
    ) -> Sequence[AgentStateTracker]:
        return [
            tracker
            for tracker in trackers
            if tracker.original_agent.resource_group_id == resource_req.resource_group_id
        ]
