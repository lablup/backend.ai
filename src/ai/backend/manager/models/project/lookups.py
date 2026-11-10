"""Lookup implementations for the group table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ProjectNameInDomainLookup(DataLookup[ProjectRow, ProjectID]):
    """Resolves a project's name within its domain into the project it names.

    The pair is the table's unique constraint: a name is only unique inside one domain.
    """

    domain_name: DomainName
    project_name: str

    @override
    def row_class(self) -> type[ProjectRow]:
        return ProjectRow

    @override
    def entity_type(self) -> EntityType:
        return ProjectEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: ProjectRow.domain_name == self.domain_name,
            lambda: ProjectRow.name == self.project_name,
        ]

    @override
    def to_entity_id(self, row: ProjectRow) -> ProjectID:
        return ProjectID(row.id)


@dataclass
class PersonalProjectOfUserLookup(DataLookup[ProjectRow, ProjectID]):
    """Resolves a user into the project that is theirs alone.

    A partial unique index holds a user to at most one, so the creating user and the
    personal type together answer with a single row.
    """

    user_id: UserID

    @override
    def row_class(self) -> type[ProjectRow]:
        return ProjectRow

    @override
    def entity_type(self) -> EntityType:
        return ProjectEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: ProjectRow.creator_id == self.user_id,
            lambda: ProjectRow.type == ProjectType.PERSONAL,
        ]

    @override
    def to_entity_id(self, row: ProjectRow) -> ProjectID:
        return ProjectID(row.id)
