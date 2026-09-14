"""Action to list all available export reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import ReportDef
from ai.backend.manager.services.export.actions.base import ExportAction


@dataclass(frozen=True)
class ListReportsAction(ExportAction):
    """Action to list all available export reports."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_reports"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class ListReportsActionResult:
    """Result of listing export reports."""

    reports: list[ReportDef]
