from abc import ABC, abstractmethod
from collections.abc import Mapping

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta

__all__ = ("AtomicBulkActionValidator", "PartialBulkActionValidator")


class AtomicBulkActionValidator(ABC):
    """Refuses a bulk action as a whole, by raising.

    Marked atomic because the run stands or falls as one; the unmarked
    :class:`PartialBulkActionValidator` is the per-entity default. Bound to the
    self-contained :class:`BaseBulkAction`, so neither leans on the legacy bases.
    """

    @abstractmethod
    async def validate(self, meta: BulkActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the validate method")


class PartialBulkActionValidator(ABC):
    """Says which of the named entities the caller may not reach, and why.

    Answers with the denials rather than raising one: a bulk run answers for every
    entity it was given, so a denial is one failed item, not a failed run.
    """

    @abstractmethod
    async def validate(self, meta: BulkActionTriggerMeta) -> Mapping[EntityIdentifier, Exception]:
        raise NotImplementedError("Subclasses must implement the validate method")
