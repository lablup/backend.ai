from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

from .base import TemplateAction


@dataclass
class UpdateClusterTemplateAction(TemplateAction):
    """Action to update an existing cluster template."""

    template_id: str
    template_data: Mapping[str, Any]
    requester_uuid: uuid.UUID
    requester_role: UserRole
    requester_domain: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return self.template_id


@dataclass
class UpdateClusterTemplateActionResult(BaseActionResult):
    """Result of updating a cluster template."""

    @override
    def entity_id(self) -> str | None:
        return None
