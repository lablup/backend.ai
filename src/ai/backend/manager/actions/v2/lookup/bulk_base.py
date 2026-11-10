from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.lookup.base import LookupKey

__all__ = (
    "BaseBulkLookupAction",
    "BaseBulkLookupActionResult",
    "BulkLookupKeyResult",
)


class BaseBulkLookupAction(ABC):
    """Base for actions that turn several external keys into internal ids at once.

    The bulk sibling of :class:`BaseLookupAction`, for the same reason the bulk write
    shape exists: the caller named the keys, so each one is answered for. Resolving them
    one run at a time would put the same read behind N records.
    """

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """Return the type of entity being looked up."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

    @abstractmethod
    def lookup_keys(self) -> Sequence[LookupKey]:
        """Return the keys being read."""
        raise NotImplementedError

    @classmethod
    def operation_type(cls) -> ActionOperationType:
        """Its own operation, as the single lookup's is."""
        return ActionOperationType.LOOKUP


@dataclass(frozen=True)
class BulkLookupKeyResult:
    """How one key of a bulk lookup fared, and what it resolved to."""

    key: LookupKey
    status: OperationStatus
    description: str
    error_code: ErrorCode | None
    entity_id: EntityIdentifier | None


class BaseBulkLookupActionResult(ABC):
    @abstractmethod
    def key_results(self) -> Sequence[BulkLookupKeyResult]:
        """Return one result per key in ``action.lookup_keys()``.

        A key that named nothing is a failed key, not a failed run: the caller asked
        about several and is answered about each.
        """
        raise NotImplementedError
