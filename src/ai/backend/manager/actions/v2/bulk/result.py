from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Self

from ai.backend.common.data.entity.action import ActionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import OperationStatus

__all__ = (
    "BulkEntityResult",
    "BasePartialBulkActionResult",
    "BulkActionResultMeta",
    "BulkActionProcessResult",
    "PartialBulkEntityResult",
    "PartialBulkResult",
)


@dataclass(frozen=True)
class BulkEntityResult:
    """How one entity of a bulk run fared."""

    entity_id: EntityIdentifier
    status: OperationStatus
    description: str
    error_code: ErrorCode | None


class BasePartialBulkActionResult(ABC):
    """The result of a run whose entities may not share one fate.

    Only such a run has anything to report per entity; one that stands or falls as a
    whole is judged by whether it raised, so it needs no result of this kind.
    """

    @abstractmethod
    def entity_results(self) -> Sequence[BulkEntityResult]:
        """Return one result per entity in ``action.entity_ids()``.

        The caller named the entities, so each one's fate is reported against that
        expectation: a partial success says SUCCESS for the entities that went
        through and ERROR for the rest.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class PartialBulkEntityResult[TData]:
    """What became of one entity of a partial bulk run, as the caller is told it.

    Carries the exception, unlike :class:`BulkEntityResult`, which carries the audit
    row's columns. The two readers want different things: the trail wants a status
    and a code, the caller wants the error to raise or report.
    """

    entity_id: EntityIdentifier
    value: TData | None
    error: Exception | None
    description: str = ""
    during_validation: bool = False

    @property
    def is_denied(self) -> bool:
        """Whether the caller was refused this entity rather than the operation failing.

        Reads the step the error came from, which is the only thing that tells the two
        apart: both carry an exception and neither carries a value.
        """
        return self.error is not None and self.during_validation

    @classmethod
    def succeeded(cls, entity_id: EntityIdentifier, value: TData, description: str = "") -> Self:
        """``description`` says what the value was, for the audit row.

        Carried rather than read off the value: what a domain's value means is the
        domain's to say, and nothing above it can read one it does not know.
        """
        return cls(entity_id=entity_id, value=value, error=None, description=description)

    @classmethod
    def nothing(cls, entity_id: EntityIdentifier, description: str = "") -> Self:
        """The operation answered for this entity and there was nothing to report.

        Not a failure: a read whose subject legitimately holds no value says so this
        way, while an id naming no row at all is a :meth:`failed` one.
        """
        return cls(entity_id=entity_id, value=None, error=None, description=description)

    @classmethod
    def failed(cls, entity_id: EntityIdentifier, error: Exception) -> Self:
        """The operation answered for this entity and could not deliver it."""
        return cls(entity_id=entity_id, value=None, error=error)

    @classmethod
    def denied(cls, entity_id: EntityIdentifier, error: Exception) -> Self:
        """Validation removed this entity, so the operation never saw it.

        Kept apart from :meth:`failed` because a denial is what the audit trail
        records as DENIED, and only the step it happened in can say so.
        """
        return cls(entity_id=entity_id, value=None, error=error, during_validation=True)


@dataclass(frozen=True)
class PartialBulkResult[TData]:
    """One answer per entity the caller named, in the order they named them.

    Fixed rather than per domain: the processor completes and orders it, which it
    could not do for a result whose shape only the domain knows.
    """

    items: Sequence[PartialBulkEntityResult[TData]]

    def values(self) -> Mapping[EntityIdentifier, TData]:
        """The entities that were delivered."""
        return {item.entity_id: item.value for item in self.items if item.value is not None}

    def errors(self) -> Mapping[EntityIdentifier, Exception]:
        """The entities that were not, the denied ones among them."""
        return {item.entity_id: item.error for item in self.items if item.error is not None}


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
