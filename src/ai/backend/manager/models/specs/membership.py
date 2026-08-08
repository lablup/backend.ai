from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import final

from ai.backend.common.data.entity.types import EntityRef, EntityType, ScopeRef
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.models.base import Base


@dataclass(frozen=True)
class ScopeMembershipEntry:
    """A member row under its parent scope."""

    member: EntityRef
    parent_scope: ScopeRef


class ScopedMembership[TRow: Base](ABC):
    """Scope membership declaration of an entity whose rows each belong to exactly
    one parent scope.

    One declaration class per entity, shared by its scoped write specs, so
    registration on create/upsert and removal on purge read the same answer. The
    ops layer records and removes the declared membership.
    """

    @abstractmethod
    def entity_type(self) -> EntityType:
        raise NotImplementedError

    @abstractmethod
    def entity_id(self, row: TRow) -> EntityID:
        raise NotImplementedError

    @abstractmethod
    def parent_scope(self, row: TRow) -> ScopeRef:
        raise NotImplementedError

    @final
    def membership_of(self, row: TRow) -> ScopeMembershipEntry:
        return ScopeMembershipEntry(
            member=EntityRef(entity_type=self.entity_type(), entity_id=self.entity_id(row)),
            parent_scope=self.parent_scope(row),
        )
