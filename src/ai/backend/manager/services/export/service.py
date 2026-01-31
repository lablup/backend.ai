"""Export service for handling export operations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .actions import (
    GetReportAction,
    GetReportActionResult,
    ListReportsAction,
    ListReportsActionResult,
)
from .actions.export_audit_logs_csv import (
    ExportAuditLogsCSVAction,
    ExportAuditLogsCSVActionResult,
)
from .actions.export_keypairs_csv import ExportKeypairsCSVAction, ExportKeypairsCSVActionResult
from .actions.export_projects_csv import ExportProjectsCSVAction, ExportProjectsCSVActionResult
from .actions.export_sessions_csv import ExportSessionsCSVAction, ExportSessionsCSVActionResult
from .actions.export_users_csv import ExportUsersCSVAction, ExportUsersCSVActionResult

if TYPE_CHECKING:
    from ai.backend.manager.repositories.export import ExportRepository

__all__ = ("ExportService",)


class ExportService:
    """Service for export operations.

    Handles listing reports, getting report details, and executing CSV exports.
    Each report type (users, sessions, projects) has its own export method.
    """

    _repository: ExportRepository

    def __init__(
        self,
        repository: ExportRepository,
    ) -> None:
        """Initialize ExportService.

        Args:
            repository: Export repository for data access
        """
        self._repository = repository

    async def list_reports(self, _action: ListReportsAction) -> ListReportsActionResult:
        """List all available export reports.

        Args:
            action: List reports action (no parameters needed)

        Returns:
            Action result containing list of report definitions
        """
        reports = self._repository.list_reports()
        return ListReportsActionResult(reports=reports)

    async def get_report(self, action: GetReportAction) -> GetReportActionResult:
        """Get a specific export report by key.

        Args:
            action: Get report action with report_key

        Returns:
            Action result containing the report definition

        Raises:
            ExportReportNotFound: If report_key is not found
        """
        report = self._repository.get_report(action.report_key)
        return GetReportActionResult(report=report)

    async def export_users_csv(self, action: ExportUsersCSVAction) -> ExportUsersCSVActionResult:
        """Execute user CSV export.

        Args:
            action: Export users CSV action with pre-built query

        Returns:
            Action result containing field names, row iterator, and filename
        """
        filename = action.filename
        if filename is None:
            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
            filename = f"users-{timestamp}.csv"

        field_names = [f.name for f in action.query.fields]
        row_iterator = self._repository.execute_export(action.query)

        return ExportUsersCSVActionResult(
            field_names=field_names,
            row_iterator=row_iterator,
            encoding=action.encoding,
            filename=filename,
        )

    async def export_sessions_csv(
        self, action: ExportSessionsCSVAction
    ) -> ExportSessionsCSVActionResult:
        """Execute session CSV export.

        Args:
            action: Export sessions CSV action with pre-built query

        Returns:
            Action result containing field names, row iterator, and filename
        """
        filename = action.filename
        if filename is None:
            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
            filename = f"sessions-{timestamp}.csv"

        field_names = [f.name for f in action.query.fields]
        row_iterator = self._repository.execute_export(action.query)

        return ExportSessionsCSVActionResult(
            field_names=field_names,
            row_iterator=row_iterator,
            encoding=action.encoding,
            filename=filename,
        )

    async def export_projects_csv(
        self, action: ExportProjectsCSVAction
    ) -> ExportProjectsCSVActionResult:
        """Execute project CSV export.

        Args:
            action: Export projects CSV action with pre-built query

        Returns:
            Action result containing field names, row iterator, and filename
        """
        filename = action.filename
        if filename is None:
            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
            filename = f"projects-{timestamp}.csv"

        field_names = [f.name for f in action.query.fields]
        row_iterator = self._repository.execute_export(action.query)

        return ExportProjectsCSVActionResult(
            field_names=field_names,
            row_iterator=row_iterator,
            encoding=action.encoding,
            filename=filename,
        )

    async def export_keypairs_csv(
        self, action: ExportKeypairsCSVAction
    ) -> ExportKeypairsCSVActionResult:
        """Execute keypair CSV export.

        Args:
            action: Export keypairs CSV action with pre-built query

        Returns:
            Action result containing field names, row iterator, and filename
        """
        filename = action.filename
        if filename is None:
            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
            filename = f"keypairs-{timestamp}.csv"

        field_names = [f.name for f in action.query.fields]
        row_iterator = self._repository.execute_export(action.query)

        return ExportKeypairsCSVActionResult(
            field_names=field_names,
            row_iterator=row_iterator,
            encoding=action.encoding,
            filename=filename,
        )

    async def export_audit_logs_csv(
        self, action: ExportAuditLogsCSVAction
    ) -> ExportAuditLogsCSVActionResult:
        """Execute audit log CSV export.

        Args:
            action: Export audit logs CSV action with pre-built query

        Returns:
            Action result containing field names, row iterator, and filename
        """
        filename = action.filename
        if filename is None:
            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
            filename = f"audit-logs-{timestamp}.csv"

        field_names = [f.name for f in action.query.fields]
        row_iterator = self._repository.execute_export(action.query)

        return ExportAuditLogsCSVActionResult(
            field_names=field_names,
            row_iterator=row_iterator,
            encoding=action.encoding,
            filename=filename,
        )
