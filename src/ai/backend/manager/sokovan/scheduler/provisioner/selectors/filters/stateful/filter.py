"""Stateful filter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.agent import AgentLimit

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
        AgentSelectionCriteria,
    )


class AbstractStatefulTrackerFilter(ABC):
    """Drops agents whose current resource state falls short; a rejected
    agent can pass again once resources are reclaimed (preemption).

    Filters only filter: they return the survivors and never raise. The
    selection pipeline decides what an emptied pool means.
    """

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def success_message(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def filter(
        self,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
        limit: AgentLimit,
    ) -> Sequence[AgentStateTracker]:
        """The trackers that stay in the running."""
        raise NotImplementedError
