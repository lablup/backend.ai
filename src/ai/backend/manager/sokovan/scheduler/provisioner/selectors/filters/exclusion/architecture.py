"""Exclusion filter: agents must serve the required architecture."""

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


class ArchitectureTrackerFilter(AbstractExclusionTrackerFilter):
    """Keeps only agents matching the requirement's architecture."""

    @override
    def name(self) -> str:
        return "architecture"

    @override
    def success_message(self) -> str:
        return "Agents with a matching architecture found"

    @override
    def failure_message(
        self,
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
    ) -> str:
        return f"no agent serves the required architecture '{resource_req.required_architecture}'"

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
            if tracker.original_agent.architecture == resource_req.required_architecture
        ]
