"""Processor package for export operations."""

from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions import (
    ExportAuditLogsCSVAction,
    ExportAuditLogsCSVActionResult,
    ExportProjectsCSVAction,
    ExportProjectsCSVActionResult,
    ExportSessionsCSVAction,
    ExportSessionsCSVActionResult,
    ExportUsersCSVAction,
    ExportUsersCSVActionResult,
    GetReportAction,
    GetReportActionResult,
    ListReportsAction,
    ListReportsActionResult,
)
from .service import ExportService

__all__ = ("ExportProcessors",)


class ExportProcessors(AbstractProcessorPackage):
    """Processor package for export operations.

    Provides processors for:
    - Listing available reports
    - Getting report metadata
    - Report-specific CSV exports (users, sessions, projects, audit-logs)
    """

    list_reports: ActionProcessor[ListReportsAction, ListReportsActionResult]
    get_report: ActionProcessor[GetReportAction, GetReportActionResult]
    export_users_csv: ActionProcessor[ExportUsersCSVAction, ExportUsersCSVActionResult]
    export_sessions_csv: ActionProcessor[ExportSessionsCSVAction, ExportSessionsCSVActionResult]
    export_projects_csv: ActionProcessor[ExportProjectsCSVAction, ExportProjectsCSVActionResult]
    export_audit_logs_csv: ActionProcessor[ExportAuditLogsCSVAction, ExportAuditLogsCSVActionResult]

    def __init__(self, service: ExportService, action_monitors: list[ActionMonitor]) -> None:
        self.list_reports = ActionProcessor(service.list_reports, action_monitors)
        self.get_report = ActionProcessor(service.get_report, action_monitors)
        self.export_users_csv = ActionProcessor(service.export_users_csv, action_monitors)
        self.export_sessions_csv = ActionProcessor(service.export_sessions_csv, action_monitors)
        self.export_projects_csv = ActionProcessor(service.export_projects_csv, action_monitors)
        self.export_audit_logs_csv = ActionProcessor(service.export_audit_logs_csv, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ListReportsAction.spec(),
            GetReportAction.spec(),
            ExportUsersCSVAction.spec(),
            ExportSessionsCSVAction.spec(),
            ExportProjectsCSVAction.spec(),
            ExportAuditLogsCSVAction.spec(),
        ]
