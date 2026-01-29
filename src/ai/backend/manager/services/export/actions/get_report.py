"""Action to get a specific export report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.repositories.base.export import ReportDef

from .base import ExportAction


@dataclass
class GetReportAction(ExportAction):
    """Action to get a specific export report by key."""

    report_key: str

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_report"

    @override
    def entity_id(self) -> str | None:
        return self.report_key


@dataclass
class GetReportActionResult(BaseActionResult):
    """Result of getting an export report."""

    report: ReportDef

    @override
    def entity_id(self) -> str | None:
        return None
