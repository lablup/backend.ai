from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

from pydantic import Field

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.session_template.types import TemplateType
from ai.backend.manager.models.session_template.upserters import SessionTemplateUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class SessionTemplateSeed(SeedItem):
    """One ``session_templates`` row, owned by the user its id names, in that user's
    domain and in the project its id names or in none."""

    id: SessionTemplateID
    user_id: UserID
    project_id: ProjectID | None = None
    type: TemplateType = TemplateType.TASK
    name: str | None = Field(default=None, max_length=128)
    is_active: bool = True
    template: dict[str, Any]

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=SessionTemplateUpserter(
                id=self.id,
                user_id=self.user_id,
                project_id=self.project_id,
                template_type=self.type,
                name=self.name,
                is_active=self.is_active,
                template=self.template,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[SessionTemplateSeed]]) -> list[SeedRejection]:
        return []
