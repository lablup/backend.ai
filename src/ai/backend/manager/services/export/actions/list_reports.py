"""Action to list all available export reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.repositories.base.export import ReportDef

from .base import ExportAction


@dataclass
class ListReportsAction(ExportAction):
    """Action to list all available export reports."""

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_reports"

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ListReportsActionResult(BaseActionResult):
    """Result of listing export reports."""

    reports: list[ReportDef]

    @override
    def entity_id(self) -> str | None:
        return None
