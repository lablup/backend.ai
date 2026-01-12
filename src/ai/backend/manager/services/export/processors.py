"""Export processors for action processing."""

from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.export.actions.export_csv import (
    ExportCsvAction,
    ExportCsvActionResult,
)
from ai.backend.manager.services.export.actions.list_reports import (
    ListReportsAction,
    ListReportsActionResult,
)
from ai.backend.manager.services.export.service import ExportService


class ExportProcessors(AbstractProcessorPackage):
    """Processors for export service actions."""

    list_reports: ActionProcessor[ListReportsAction, ListReportsActionResult]
    export_csv: ActionProcessor[ExportCsvAction, ExportCsvActionResult]

    def __init__(
        self,
        service: ExportService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        """Initialize export processors.

        Args:
            service: Export service instance
            action_monitors: List of action monitors for observability
        """
        self.list_reports = ActionProcessor(service.list_reports, action_monitors)
        self.export_csv = ActionProcessor(service.export_csv, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        """Return list of supported action specifications."""
        return [
            ListReportsAction.spec(),
            ExportCsvAction.spec(),
        ]
