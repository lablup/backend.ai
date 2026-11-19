from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session_template.types import (
    SessionTemplateWithOwnerEmailAndProjectName,
)

from .base import TemplateGlobalAction


@dataclass(frozen=True)
class GlobalListClusterTemplatesAction(TemplateGlobalAction):
    """List the cluster templates of every user and project."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_list_cluster_templates"


@dataclass(frozen=True)
class GlobalListClusterTemplatesActionResult:
    entries: list[SessionTemplateWithOwnerEmailAndProjectName]
