"""Action to get a specific export report, open to every authenticated caller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import ReportDef
from ai.backend.manager.services.export.actions.base import ExportAction


@dataclass(frozen=True)
class PublicGetReportAction(ExportAction):
    """Read a report definition before an export authorized against its own scope."""

    report_key: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GlobalEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_get_report"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class PublicGetReportActionResult:
    report: ReportDef
