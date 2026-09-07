from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.common.data.idle_checker.types import IdleCheckerSpec
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.errors.idle_checker import (
    IdleCheckerAssignmentAlreadyExists,
    IdleCheckerAssignmentScopeNotFound,
    IdleCheckerNotFound,
)
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.relation import RelationCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck, PreconditionCheck
from ai.backend.manager.models.user.row import UserRow


@dataclass
class IdleCheckerCreator(GlobalEntityCreator[IdleCheckerRow, IdleCheckerData]):
    """Creator for an idle checker definition in the global catalog."""

    name: str
    description: str | None
    target_session_types: list[SessionTypes]
    initial_grace_period_seconds: int
    spec: IdleCheckerSpec

    @override
    def entity_id(self, row: IdleCheckerRow) -> IdleCheckerID:
        return IdleCheckerID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> IdleCheckerRow:
        return IdleCheckerRow(
            name=self.name,
            description=self.description,
            target_session_types=self.target_session_types,
            initial_grace_period_seconds=self.initial_grace_period_seconds,
            spec=self.spec,
        )

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return row.to_data()


@dataclass
class IdleCheckerAssignmentCreator(
    RelationCreator[EntityIdentifier, IdleCheckerID, IdleCheckerBindingRow]
):
    """Links a scope (a domain, project, resource group or user) to an idle checker
    (the target). ``enabled`` is the row's lifecycle column and its initial value."""

    enabled: bool

    @override
    def precondition_checks(
        self, scope: EntityIdentifier, target: IdleCheckerID
    ) -> Sequence[PreconditionCheck]:
        """The scope row must be there: its side carries no foreign key. A scope type
        outside the four the table takes is refused the same way."""
        columns: dict[EntityType, InstrumentedAttribute[Any]] = {
            DOMAIN_ENTITY_TYPE: DomainRow.id,
            PROJECT_ENTITY_TYPE: ProjectRow.id,
            RESOURCE_GROUP_ENTITY_TYPE: ResourceGroupRow.id,
            USER_ENTITY_TYPE: UserRow.uuid,
        }
        column = columns.get(scope.entity_type())
        finder = sa.select(sa.literal(True))
        if column is not None:
            finder = finder.where(sa.not_(sa.exists(sa.select(column).where(column == scope))))
        return (
            PreconditionCheck(
                finder=finder,
                error=IdleCheckerAssignmentScopeNotFound(f"{scope.entity_type()}:{scope}"),
            ),
        )

    @override
    def row_class(self) -> type[IdleCheckerBindingRow]:
        return IdleCheckerBindingRow

    @override
    def build_row(self, scope: EntityIdentifier, target: IdleCheckerID) -> IdleCheckerBindingRow:
        return IdleCheckerBindingRow(
            scope_type=scope.entity_type(),
            scope_id=scope,
            idle_checker_id=target,
            enabled=self.enabled,
        )

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=IdleCheckerAssignmentAlreadyExists(
                    "The idle checker is already bound to the scope"
                ),
                constraint_name="uq_idle_checker_bindings_checker_scope",
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=IdleCheckerNotFound("The idle checker to bind does not exist"),
                constraint_name="fk_idle_checker_bindings_idle_checker_id",
            ),
        )
