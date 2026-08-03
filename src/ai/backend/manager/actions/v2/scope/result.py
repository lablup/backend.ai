from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.exception import ErrorCode
from ai.backend.common.identifier.action import ActionID
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.types import OperationStatus

__all__ = (
    "BaseScopeActionResult",
    "ScopeActionResultMeta",
    "ScopeActionProcessResult",
)


class BaseScopeActionResult(ABC):
    @abstractmethod
    def entity_ids(self) -> Sequence[EntityID]:
        """Return the entities the run affected, empty if it affected none.

        No per-entity status: the caller named a scope, not entities, so there is no
        per-entity expectation to report against — the run's own status covers it.
        """
        raise NotImplementedError


@dataclass
class ScopeActionResultMeta:
    """Outcome metadata for a scope action run.

    ``scope_targets`` is what was requested; ``entity_ids`` is what the run actually
    touched. The audit trail is keyed on the latter, so a run over several scopes
    still writes one row per entity rather than one per scope.
    """

    action_id: ActionID
    scope_targets: Sequence[ScopeRef]
    entity_ids: Sequence[EntityID]
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


@dataclass
class ScopeActionProcessResult:
    meta: ScopeActionResultMeta
