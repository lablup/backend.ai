from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

from .base import TemplateAction


@dataclass
class GetClusterTemplateAction(TemplateAction):
    """Action to get a single cluster template by ID."""

    template_id: str
    requester_uuid: uuid.UUID
    requester_role: UserRole
    requester_domain: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.template_id


@dataclass
class GetClusterTemplateActionResult(BaseActionResult):
    """Result of getting a cluster template."""

    template: dict[str, Any]

    @override
    def entity_id(self) -> str | None:
        return None
