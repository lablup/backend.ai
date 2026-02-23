from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


@dataclass
class ProjectConfigAction(BaseAction):
    """Base action for project config operations."""

    project_id_or_name: uuid.UUID | str
    domain_name: str | None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PROJECT_CONFIG
