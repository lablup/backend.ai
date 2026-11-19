from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session_template.types import SessionTemplateData

from .base import TemplateAction


@dataclass
class GetClusterTemplateAction(TemplateAction):
    """Action to get a single cluster template by ID."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_cluster_template"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetClusterTemplateActionResult:
    """Result of getting a cluster template."""

    template: SessionTemplateData
