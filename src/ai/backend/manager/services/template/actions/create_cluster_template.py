from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user.row import UserRole

from .base import TemplateProjectScopeAction, TemplateScopeActionResult


@dataclass
class CreateClusterTemplateAction(TemplateProjectScopeAction):
    """Action to create a cluster template."""

    domain_name: str
    requester_uuid: UserID
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

    id: SessionTemplateID
    user: UserID

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (self.id,)
