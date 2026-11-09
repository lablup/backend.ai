"""Upsert specs for session templates."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.session_template.types import TemplateType
from ai.backend.manager.models.session_template.row import SessionTemplateRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter
from ai.backend.manager.models.user.row import UserRow

__all__ = ("SessionTemplateUpserter",)


@dataclass
class SessionTemplateUpserter(EntityUpserter[SessionTemplateRow, SessionTemplateID]):
    """Write a session template under its stated id, created in its owner and its project
    as :class:`SessionTemplateCreator` is. Conflict key: id. The owner, the owner's domain
    and the project are written on insert only."""

    id: SessionTemplateID
    user_id: UserID
    project_id: ProjectID | None
    template_type: TemplateType
    name: str | None
    is_active: bool
    template: Mapping[str, Any]

    @override
    def entity_id(self, row: SessionTemplateRow) -> SessionTemplateID:
        return SessionTemplateID(row.id)

    @override
    def created_in(self, row: SessionTemplateRow) -> Collection[EntityIdentifier]:
        scopes: list[EntityIdentifier] = [UserID(row.user_uuid)]
        if row.group_id is not None:
            scopes.append(ProjectID(row.group_id))
        return scopes

    @override
    def row_class(self) -> type[SessionTemplateRow]:
        return SessionTemplateRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        """An owner naming no user leaves ``domain_name`` NULL, which the column refuses."""
        return {
            "id": self.id,
            "user_uuid": self.user_id,
            "domain_name": sa.select(UserRow.domain_name)
            .where(UserRow.uuid == self.user_id)
            .scalar_subquery(),
            "group_id": self.project_id,
            **self.build_update_values(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "type": self.template_type,
            "name": self.name,
            "is_active": self.is_active,
            "template": dict(self.template),
        }

    @override
    def to_data(self, row: SessionTemplateRow) -> SessionTemplateID:
        return SessionTemplateID(row.id)
