from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session_template.types import (
    SessionTemplateWithOwnerEmailAndProjectName,
)

from .base import TemplateScopeActionResult, TemplateUserScopeAction


@dataclass
class ListClusterTemplatesAction(TemplateUserScopeAction):
    """List the cluster templates the requester or a project they joined holds."""

    group_id_filter: ProjectID | None = None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_cluster_templates"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListClusterTemplatesActionResult(TemplateScopeActionResult):
    """Result of listing cluster templates."""

    entries: list[SessionTemplateWithOwnerEmailAndProjectName] = field(default_factory=list)
