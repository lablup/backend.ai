"""Insert specs of the v2 lineage.

The family roots below are deliberately unrelated — no common ABC. See AGENTS.md
in this package before typing anything against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence
from typing import final

from ai.backend.common.data.entity.types import ScopeRef, ScopeType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.role_template import RoleTemplateSource
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


class GlobalEntityCreator[TRow: Base, TData](ABC):
    """Insert spec of a global entity — system-wide state outside the scope
    hierarchy; creating a row makes no scope of it and joins nothing."""

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_row(self) -> TRow:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class EntityCreator[TRow: Base, TData](ABC):
    """Insert spec of an entity: every entity doubles as a scope, so creating a
    row always provisions its virtual scope node (self membership and self
    binding) and joins the scopes ``member_of`` declares.

    The entity's identity is its scope identity — one (``scope_type``,
    ``scope_id``) pair serves both sides. Answer ``scope_type()`` /
    ``scope_id(row)``; ``scope_of()`` is fixed. The spec knows nothing about
    roles; entities that allow role presets use
    :class:`RoleManagedEntityCreator`.
    """

    @abstractmethod
    def scope_type(self) -> ScopeType:
        """The scope type every row of this entity becomes; known before the insert."""
        raise NotImplementedError

    @abstractmethod
    def scope_id(self, row: TRow) -> ScopeID:
        """The new scope's id, read off the settled row; not necessarily the primary key."""
        raise NotImplementedError

    @final
    def scope_of(self, row: TRow) -> ScopeRef:
        return ScopeRef(scope_type=self.scope_type(), scope_id=self.scope_id(row))

    @abstractmethod
    def member_of(self, row: TRow) -> Collection[ScopeRef]:
        """The existing scopes the new entity joins as a member (a project joins
        its domain; a keypair joins its user). Empty for a top-level scope.
        Carries no permission cap: capped sharing is the object-sharing
        mechanism, not creation."""
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_row(self) -> TRow:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class RoleManagedEntityCreator[TRow: Base, TData](RoleTemplateSource[TRow], ABC):
    """Insert spec of a role-managed entity (domain/project/user): the entity
    creation plus the role-preset declaration.

    Deliberately NOT an :class:`EntityCreator` subtype — the entity hooks are
    duplicated instead — so a role-managed spec cannot flow through the plain
    ``create_entity`` path and silently skip its preset roles; only the
    role-managed ops methods accept this type.
    """

    @abstractmethod
    def scope_type(self) -> ScopeType:
        """The scope type every row of this entity becomes; known before the insert."""
        raise NotImplementedError

    @abstractmethod
    def scope_id(self, row: TRow) -> ScopeID:
        """The new scope's id, read off the settled row; not necessarily the primary key."""
        raise NotImplementedError

    @final
    def scope_of(self, row: TRow) -> ScopeRef:
        return ScopeRef(scope_type=self.scope_type(), scope_id=self.scope_id(row))

    @abstractmethod
    def member_of(self, row: TRow) -> Collection[ScopeRef]:
        """The existing scopes the new entity joins as a member; empty for a
        top-level scope. Carries no permission cap."""
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_row(self) -> TRow:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class FieldEntityCreator[TOwnerID: EntityID, TRow: Base, TData](ABC):
    """Insert spec of a field row — a row owned by another entity.

    Built only from the owner's settled identifier (e.g. a just-created parent's
    id), so a field row cannot be created standalone. It becomes no scope and
    joins nothing: writing a field row is authorized through the owner, like an
    update to the owning entity.
    """

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def build_row(self, owner_id: TOwnerID) -> TRow:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError
