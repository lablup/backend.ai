"""Stateful filter: agents must be below the per-agent container cap."""

from __future__ import annotations

from collections.abc import Sequence
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


class ContainerLimitTrackerFilter(AbstractStatefulTrackerFilter):
    """Keeps agents below the configured max container count."""

    @override
    def name(self) -> str:
        return "container-limit"

    @override
    def success_message(self) -> str:
        return "Agents below the container limit found"

    @override
    def filter(
        self,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
        limit: AgentLimit,
    ) -> Sequence[AgentStateTracker]:
        if limit.max_container_count is None:
            return trackers
        return [
            tracker
            for tracker in trackers
            if tracker.current_container_count() < limit.max_container_count
        ]
