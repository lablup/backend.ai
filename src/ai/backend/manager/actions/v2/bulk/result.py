from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.exception import ErrorCode
from ai.backend.common.identifier.action import ActionID
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.types import OperationStatus

__all__ = (
    "BulkEntityResult",
    "BaseBulkActionResult",
    "BulkActionResultMeta",
    "BulkActionProcessResult",
)


@dataclass(frozen=True)
class BulkEntityResult:
    """How one entity of a bulk run fared."""

    entity_id: EntityID
    status: OperationStatus
    description: str
    error_code: ErrorCode | None


class BaseBulkActionResult(ABC):
    @abstractmethod
    def entity_results(self) -> Sequence[BulkEntityResult]:
        """Return one result per entity in ``action.entity_ids()``.

        The caller named the entities, so each one's fate is reported against that
        expectation: a partial success says SUCCESS for the entities that went
        through and ERROR for the rest.
        """
        raise NotImplementedError


@dataclass
class BulkActionResultMeta:
    """Outcome metadata for a bulk action run, resolved for each entity separately.

    The run has no status of its own: every entity carries one, and each audit row
    covers a single entity. Where the metrics need one value per run, the Prometheus
    monitor derives it — that is a metrics concern, not a fact about the run.
    """

    action_id: ActionID
    entity_results: Sequence[BulkEntityResult]
    started_at: datetime
    ended_at: datetime
    duration: timedelta


@dataclass
class BulkActionProcessResult:
    meta: BulkActionResultMeta
