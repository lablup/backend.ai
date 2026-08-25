from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

from .base import TemplateProjectScopeAction, TemplateScopeActionResult


@dataclass
class CreateClusterTemplateAction(TemplateProjectScopeAction):
    """Action to create a cluster template."""

    domain_name: str
    requester_uuid: uuid.UUID
    requester_access_key: str
    requester_role: UserRole
    requester_domain: str
    owner_access_key: str | None
    template_data: Mapping[str, Any]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_cluster_template"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateClusterTemplateActionResult(TemplateScopeActionResult):
    """Result of creating a cluster template."""

    id: str
    user: str
