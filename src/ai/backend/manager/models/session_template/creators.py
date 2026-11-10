"""Creator specs for session templates."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.session_template.types import TemplateType
from ai.backend.manager.models.session_template.row import SessionTemplateRow
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class SessionTemplateCreator(EntityCreator[SessionTemplateRow, SessionTemplateID]):
    """Creator for one session template, created in its owner and in its project."""

    template_id: SessionTemplateID
    template_type: TemplateType
    domain_name: str
    user_uuid: UserID
    group_id: ProjectID | None
    name: str | None
    template: Mapping[str, Any]
    created_at: datetime

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
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> SessionTemplateRow:
        return SessionTemplateRow(
            id=self.template_id,
            created_at=self.created_at,
            domain_name=self.domain_name,
            group_id=self.group_id,
            user_uuid=self.user_uuid,
            name=self.name,
            template=dict(self.template),
            type=self.template_type,
        )

    @override
    def to_data(self, row: SessionTemplateRow) -> SessionTemplateID:
        return SessionTemplateID(row.id)
