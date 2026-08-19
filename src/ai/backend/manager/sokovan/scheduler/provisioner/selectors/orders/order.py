"""Tracker order interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
        AgentSelectionCriteria,
    )


class AbstractTrackerOrder(ABC):
    """Narrows the candidates to a preferred tier; never excludes — when
    every candidate ranks the same, all of them stay."""

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def rank(self, tracker: AgentStateTracker, criteria: AgentSelectionCriteria) -> int:
        """Preference rank of one tracker (lower is preferred)."""
        raise NotImplementedError
