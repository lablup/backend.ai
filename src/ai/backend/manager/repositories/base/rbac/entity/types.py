"""Shared value types for the entity CRUD inputs of the RBAC ops layer."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.common.data.entity.types import EntityRef, ScopeRef
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.identifier.user import UserID


class ScopeMembership(ABC):
    """A membership edge: an entity joins a scope as a member."""

    @abstractmethod
    def scope(self) -> ScopeRef:
        """Return the scope being joined."""
        raise NotImplementedError

    @abstractmethod
    def entity_ref(self) -> EntityRef:
        """Return the member entity."""
        raise NotImplementedError

    @abstractmethod
    def permission_cap(self) -> Permission | None:
        """Return the cap on the permissions the membership conveys, or ``None``
        for no ceiling."""
        raise NotImplementedError

    @abstractmethod
    def assign_role_on(self) -> UserID | None:
        """Return the user granted the scope's ``auto_assign`` roles by this
        membership, or ``None`` to grant none."""
        raise NotImplementedError
