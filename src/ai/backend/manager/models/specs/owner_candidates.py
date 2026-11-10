"""Owner candidate specs: every entity a field row with several owners belongs to."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType, FieldIdentifier

__all__ = ("FieldOwnerCandidates",)


class FieldOwnerCandidates[TFieldID: FieldIdentifier](ABC):
    """The owners of a field row that belongs to several entities at once.

    An operation on such a row is answered for by any one owner the caller may reach.
    """

    @abstractmethod
    def owners_of(
        self, field_ids: Sequence[TFieldID]
    ) -> Sequence[sa.sql.Select[tuple[TFieldID, uuid.UUID, EntityType]]]:
        """One query per kind of owner; a row is (field row id, owner entity id, owner
        entity type)."""
        raise NotImplementedError
