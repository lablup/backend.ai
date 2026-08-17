"""Insert specs of the v2 lineage.

The roots below are deliberately unrelated — no common ABC. See AGENTS.md
in this package before typing anything against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.role_template import RoleTemplateSource
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


class GlobalEntityCreator[TRow: Base, TData](ABC):
    """Insert spec of a global entity: an entity that belongs under no other scope.

    Creating a row provisions its virtual scope node exactly as :class:`EntityCreator`
    does — rows are created under a global entity too (an image under its container
    registry), so it has to be namable in the graph. What it does not have is
    ``member_of``: it joins nothing, and the missing hook is what says so.
    """

    @abstractmethod
    def entity_id(self, row: TRow) -> EntityIdentifier:
        """The entity's id, read off the settled row; not necessarily the primary key.

        Answers the type too, so nothing declares it separately."""
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


class EntityCreator[TRow: Base, TData](ABC):
    """Insert spec of an entity: creating a row always provisions it in the RBAC graph
    (its virtual scope node, self membership and self binding) and joins the entities
    ``member_of`` declares.

    The spec knows nothing about roles; entities that allow role presets use
    :class:`RoleManagedEntityCreator`.
    """

    @abstractmethod
    def entity_id(self, row: TRow) -> EntityIdentifier:
        """The entity's id, read off the settled row; not necessarily the primary key.

        Answers the type too, so nothing declares it separately."""
        raise NotImplementedError

    @abstractmethod
    def member_of(self, row: TRow) -> Collection[EntityIdentifier]:
        """The existing entities the new one joins as a member (a project joins its
        domain; a keypair joins its user). Empty for a top-level entity. Carries no
        permission cap: capped sharing is the object-sharing mechanism, not creation."""
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
    def entity_id(self, row: TRow) -> EntityIdentifier:
        """The entity's id, read off the settled row; not necessarily the primary key.

        Answers the type too, so nothing declares it separately."""
        raise NotImplementedError

    @abstractmethod
    def member_of(self, row: TRow) -> Collection[EntityIdentifier]:
        """The existing entities the new one joins as a member; empty for a top-level
        entity. Carries no permission cap."""
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


class FieldCreator[TOwnerID: EntityIdentifier, TRow: Base, TData](ABC):
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
