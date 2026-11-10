from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateAction


@dataclass
class DeleteClusterTemplateAction(TemplateAction):
    """Action to soft-delete a cluster template."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_cluster_template"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteClusterTemplateActionResult:
    """Result of deleting a cluster template."""
