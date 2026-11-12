"""EntityCreator implementations for the system session environ repository."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.system_session_environ import (
    SystemSessionEnvironID,
    SystemSessionEnvironScopeID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.errors.repository import (
    CheckConstraintViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.errors.system_session_environ import (
    InvalidSystemSessionEnvironKey,
    SystemSessionEnvironKeyConflict,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.specs.creator import GuardedEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck, PreconditionCheck
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)

__all__ = ("SystemSessionEnvironCreator",)


@dataclass(frozen=True)
class SystemSessionEnvironCreator(
    GuardedEntityCreator[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """Insert spec of a binding at its owner: the public entity, a domain or a project.

    ``scope_id`` carries no foreign key, so a domain or a project that is not there
    refuses the write before the graph is asked for its node.
    """

    owner: EntityIdentifier
    value_source: SystemSessionEnvironValueSource
    key: str

    @override
    def precondition_checks(self) -> Sequence[PreconditionCheck]:
        match SystemSessionEnvironScopeType.of_owner(self.owner):
            case SystemSessionEnvironScopeType.PUBLIC:
                return ()
            case SystemSessionEnvironScopeType.DOMAIN:
                return (
                    PreconditionCheck(
                        finder=sa.select(sa.literal(True)).where(
                            sa.not_(
                                sa.exists(sa.select(DomainRow.id).where(DomainRow.id == self.owner))
                            )
                        ),
                        error=DomainNotFound(f"Domain {self.owner} does not exist"),
                    ),
                )
            case SystemSessionEnvironScopeType.PROJECT:
                return (
                    PreconditionCheck(
                        finder=sa.select(sa.literal(True)).where(
                            sa.not_(
                                sa.exists(
                                    sa.select(ProjectRow.id).where(ProjectRow.id == self.owner)
                                )
                            )
                        ),
                        error=ProjectNotFound(f"Project {self.owner} does not exist"),
                    ),
                )

    @override
    def entity_id(self, row: SystemSessionEnvironRow) -> SystemSessionEnvironID:
        return SystemSessionEnvironID(row.id)

    @override
    def created_in(self, row: SystemSessionEnvironRow) -> Collection[EntityIdentifier]:
        match SystemSessionEnvironScopeType.of_owner(self.owner):
            case SystemSessionEnvironScopeType.PUBLIC:
                return (
                    global_entity_id(GlobalEntityName.GLOBAL),
                    global_entity_id(GlobalEntityName.PUBLIC),
                )
            case SystemSessionEnvironScopeType.DOMAIN | SystemSessionEnvironScopeType.PROJECT:
                return (self.owner,)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_system_session_environ_key",
                error=SystemSessionEnvironKeyConflict(),
            ),
            IntegrityErrorCheck(
                violation_type=CheckConstraintViolationError,
                constraint_name="ck_system_session_environ_key_is_environ_name",
                error=InvalidSystemSessionEnvironKey(),
            ),
        )

    @override
    def build_row(self) -> SystemSessionEnvironRow:
        return SystemSessionEnvironRow(
            key=self.key,
            scope_type=SystemSessionEnvironScopeType.of_owner(self.owner),
            scope_id=SystemSessionEnvironScopeID(self.owner),
            value_source=self.value_source,
        )

    @override
    def to_data(self, row: SystemSessionEnvironRow) -> SystemSessionEnvironData:
        return SystemSessionEnvironSearchableFields.own.to_data(row)
