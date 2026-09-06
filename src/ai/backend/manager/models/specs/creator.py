"""Insert specs of the v2 lineage.

The roots below are deliberately unrelated — no common ABC — with one exception: an
entity creator answers preconditions, and the one that has none says so once rather
than every spec repeating it. See AGENTS.md in this package before typing anything
against more than one of them.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    FieldData,
    FieldIdentifier,
)
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.role_template import RoleTemplateSource
from ai.backend.manager.models.specs.types import IntegrityErrorCheck, PreconditionCheck


class GlobalEntityCreator[TRow: Base, TData](ABC):
    """Insert spec of a global entity: an entity that belongs under no other scope.

    Creating a row provisions its virtual entity node exactly as :class:`EntityCreator`
    does — rows are created under a global entity too (an image under its container
    registry), so it has to be namable in the graph. What it does not have is
    ``created_in``: it is created in no scope, and the missing hook is what says so.
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


class GuardedEntityCreator[TRow: Base, TData](ABC):
    """Insert spec of an entity that declines to write unless the graph allows it.

    The same insert :class:`EntityCreator` describes, behind preconditions the database
    cannot state as constraints of its own: a state elsewhere that makes the write
    wrong rather than impossible. What to look for is declared, not executed, so the
    spec stays a value and the read runs where the write does.

    The guard an updater or a purger carries is a different thing: a condition on the
    row already named, riding on the statement. This names rows in another table, and
    finding one raises.

    The root every entity creator shares, so one ops path serves both and a spec
    carrying refusals cannot reach a path that would skip them: the write always runs
    them, and a spec with none answers an empty list once.
    """

    @abstractmethod
    def precondition_checks(self) -> Sequence[PreconditionCheck]:
        """What must not be there for this write to stand."""
        raise NotImplementedError

    @abstractmethod
    def entity_id(self, row: TRow) -> EntityIdentifier:
        """The entity's id, read off the settled row; not necessarily the primary key.

        Answers the type too, so nothing declares it separately."""
        raise NotImplementedError

    @abstractmethod
    def created_in(self, row: TRow) -> Collection[EntityIdentifier]:
        """The scopes the new entity is created in. Each owns it and governs it."""
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


class EntityCreator[TRow: Base, TData](GuardedEntityCreator[TRow, TData], ABC):
    """Insert spec of an entity nothing outside the row can refuse.

    Everything :class:`GuardedEntityCreator` describes, with no preconditions: the
    database's own constraints are the whole of what can turn this write away. A spec
    that needs more inherits the guarded root directly rather than answering here.

    The spec knows nothing about roles; entities that allow role presets use
    :class:`RoleManagedEntityCreator`.
    """

    @final
    @override
    def precondition_checks(self) -> Sequence[PreconditionCheck]:
        return ()


class RoleManagedGlobalEntityCreator[TRow: Base, TData](RoleTemplateSource[TRow], ABC):
    """Insert spec of a role-managed entity created in no scope (domain, resource
    group): what :class:`GlobalEntityCreator` writes, plus the preset roles the
    role-template declares.

    Deliberately NOT a :class:`GlobalEntityCreator` subtype — the entity hooks are
    duplicated instead — so a role-managed spec cannot flow through the plain
    ``create_global_entity`` path and silently skip its preset roles; only the
    role-managed ops methods accept this type.
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


class RoleManagedEntityCreator[TRow: Base, TData](RoleTemplateSource[TRow], ABC):
    """Insert spec of a role-managed entity created in a scope (project, user): what
    :class:`EntityCreator` writes, plus the preset roles the role-template declares.

    Deliberately NOT an :class:`EntityCreator` subtype, for the same reason
    :class:`RoleManagedGlobalEntityCreator` is not a global one.
    """

    @abstractmethod
    def entity_id(self, row: TRow) -> EntityIdentifier:
        """The entity's id, read off the settled row; not necessarily the primary key.

        Answers the type too, so nothing declares it separately."""
        raise NotImplementedError

    @abstractmethod
    def created_in(self, row: TRow) -> Collection[EntityIdentifier]:
        """The scopes the new entity is created in (a project's domain); each owns it
        and governs it, as for :class:`EntityCreator`."""
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


@dataclass(frozen=True)
class FieldToCreate[TOwnerID: EntityIdentifier, TRow: Base, TData: FieldData]:
    """One field row to insert, under the owner named beside it.

    Carried together so a batch may reach several owners at once without the two
    falling out of step.
    """

    owner_id: TOwnerID
    creator: FieldCreator[TOwnerID, TRow, TData]


class FieldRowCreator[TRow: Base, TData: FieldData](ABC):
    """What every insert spec of a field row has, whoever owns it."""

    @abstractmethod
    def field_id(self, row: TRow) -> FieldIdentifier:
        """The row's id, read off the settled row, for the rows it owns to be built under.

        Takes the row because the id does not exist before the insert.
        """
        raise NotImplementedError

    @abstractmethod
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        raise NotImplementedError

    @abstractmethod
    def to_data(self, row: TRow) -> TData:
        raise NotImplementedError


class FieldCreator[TOwnerID: EntityIdentifier, TRow: Base, TData: FieldData](
    FieldRowCreator[TRow, TData], ABC
):
    """Insert spec of a field row — a row owned by another entity.

    Built only from the owner's settled identifier (e.g. a just-created parent's
    id), so a field row cannot be created standalone. It becomes no scope and
    joins nothing: writing a field row is authorized through the owner, like an
    update to the owning entity.
    """

    @abstractmethod
    def build_row(self, owner_id: TOwnerID) -> TRow:
        raise NotImplementedError


class DanglingFieldCreator[TRow: Base, TData: FieldData](FieldRowCreator[TRow, TData], ABC):
    """Insert spec of a field row written without an owner to build under.

    No owner names it, so what the row says about the entity it concerns is the spec's
    own value like every other column — the kind it is about where there is one, nothing
    where there is not. An operation that names scopes and no entity type is the latter.

    Reachable only by a read that names no owner either.
    """

    @abstractmethod
    def build_row(self) -> TRow:
        """Build the row, which no owner names."""
        raise NotImplementedError


@dataclass(frozen=True)
class NestedFieldToCreate[TOwnerID: FieldIdentifier, TRow: Base, TData: FieldData]:
    """One nested row to insert, under the field row named beside it.

    What :class:`FieldToCreate` is to a field row, this is to a nested one: a batch
    may reach several owners at once without the two falling out of step.
    """

    owner_id: TOwnerID
    creator: NestedFieldCreator[TOwnerID, TRow, TData]


class NestedFieldCreator[TOwnerID: FieldIdentifier, TRow: Base, TData: FieldData](ABC):
    """Insert spec of a field row another field row owns.

    What :class:`FieldCreator` is to an entity, this is to a field: built only from the
    owner's settled identifier, so it cannot be created standalone. Which entity answers
    for it is what the owner lookup reads, however many rows it joins through.
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
