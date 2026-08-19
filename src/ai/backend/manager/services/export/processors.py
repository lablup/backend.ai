"""Processor package for export operations."""

from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor

from .actions import (
    ExportAuditLogsCSVAction,
    ExportAuditLogsCSVActionResult,
    ExportKeypairsCSVAction,
    ExportKeypairsCSVActionResult,
    ExportMyKeypairsCSVAction,
    ExportMyKeypairsCSVActionResult,
    ExportMySessionsCSVAction,
    ExportMySessionsCSVActionResult,
    ExportProjectsCSVAction,
    ExportProjectsCSVActionResult,
    ExportSessionsByProjectCSVAction,
    ExportSessionsByProjectCSVActionResult,
    ExportSessionsCSVAction,
    ExportSessionsCSVActionResult,
    ExportUsersByDomainCSVAction,
    ExportUsersByDomainCSVActionResult,
    ExportUsersCSVAction,
    ExportUsersCSVActionResult,
    GetReportAction,
    GetReportActionResult,
    ListReportsAction,
    ListReportsActionResult,
)
from .service import ExportService

__all__ = ("ExportProcessors",)


class ExportProcessors:
    """Processor package for export operations.

    Provides processors for:
    - Listing available reports
    - Getting report metadata
    - Report-specific CSV exports (users, sessions, projects, keypairs, audit-logs)
    """

    list_reports: GlobalActionProcessor[ListReportsAction, ListReportsActionResult]
    get_report: GlobalActionProcessor[GetReportAction, GetReportActionResult]
    export_users_csv: GlobalActionProcessor[ExportUsersCSVAction, ExportUsersCSVActionResult]
    export_sessions_csv: GlobalActionProcessor[
        ExportSessionsCSVAction, ExportSessionsCSVActionResult
    ]
    export_projects_csv: GlobalActionProcessor[
        ExportProjectsCSVAction, ExportProjectsCSVActionResult
    ]
    export_keypairs_csv: GlobalActionProcessor[
        ExportKeypairsCSVAction, ExportKeypairsCSVActionResult
    ]
    export_audit_logs_csv: GlobalActionProcessor[
        ExportAuditLogsCSVAction, ExportAuditLogsCSVActionResult
    ]
    export_sessions_by_project_csv: ScopeActionProcessor[
        ExportSessionsByProjectCSVAction, ExportSessionsByProjectCSVActionResult
    ]
    export_users_by_domain_csv: ScopeActionProcessor[
        ExportUsersByDomainCSVAction, ExportUsersByDomainCSVActionResult
    ]
    export_my_sessions_csv: ScopeActionProcessor[
        ExportMySessionsCSVAction, ExportMySessionsCSVActionResult
    ]
    export_my_keypairs_csv: ScopeActionProcessor[
        ExportMyKeypairsCSVAction, ExportMyKeypairsCSVActionResult
    ]

    def __init__(self, group: ProcessorGroup[Any], service: ExportService) -> None:
        self.list_reports = group.global_scope(ListReportsAction, service.list_reports)
        self.get_report = group.global_scope(GetReportAction, service.get_report)
        self.export_users_csv = group.global_scope(ExportUsersCSVAction, service.export_users_csv)
        self.export_sessions_csv = group.global_scope(
            ExportSessionsCSVAction, service.export_sessions_csv
        )
        self.export_projects_csv = group.global_scope(
            ExportProjectsCSVAction, service.export_projects_csv
        )
        self.export_keypairs_csv = group.global_scope(
            ExportKeypairsCSVAction, service.export_keypairs_csv
        )
        self.export_audit_logs_csv = group.global_scope(
            ExportAuditLogsCSVAction, service.export_audit_logs_csv
        )
        self.export_sessions_by_project_csv = group.scope(
            ExportSessionsByProjectCSVAction, service.export_sessions_by_project_csv
        )
        self.export_users_by_domain_csv = group.scope(
            ExportUsersByDomainCSVAction, service.export_users_by_domain_csv
        )
        self.export_my_sessions_csv = group.scope(
            ExportMySessionsCSVAction, service.export_my_sessions_csv
        )
        self.export_my_keypairs_csv = group.scope(
            ExportMyKeypairsCSVAction, service.export_my_keypairs_csv
        )
