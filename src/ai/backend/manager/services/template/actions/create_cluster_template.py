from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateAction


@dataclass
class CreateClusterTemplateAction(TemplateAction):
    """Action to create a cluster template."""

    domain_name: str
    user_uuid: uuid.UUID
    group_id: uuid.UUID
    template_data: Mapping[str, Any]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class CreateClusterTemplateActionResult(BaseActionResult):
    """Result of creating a cluster template."""

    id: str
    user: str

    @override
    def entity_id(self) -> str | None:
        return self.id
