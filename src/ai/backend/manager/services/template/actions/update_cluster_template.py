from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType

from .base import TemplateAction


@dataclass
class UpdateClusterTemplateAction(TemplateAction):
    """Action to update an existing cluster template."""

    template_data: Mapping[str, Any]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_cluster_template"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateClusterTemplateActionResult:
    """Result of updating a cluster template."""
