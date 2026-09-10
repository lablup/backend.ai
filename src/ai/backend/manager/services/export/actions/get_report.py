"""Action to get a specific export report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import ReportDef
from ai.backend.manager.services.export.actions.base import ExportAction


@dataclass(frozen=True)
class GetReportAction(ExportAction):
    """Action to get a specific export report by key."""

    report_key: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_report"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class GetReportActionResult:
    """Result of getting an export report."""

    report: ReportDef
