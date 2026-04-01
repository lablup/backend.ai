"""Export report registry base class."""

from __future__ import annotations

from ai.backend.manager.repositories.base.export import ReportDef
from ai.backend.manager.repositories.export.reports.audit_log import AUDIT_LOG_REPORT
from ai.backend.manager.repositories.export.reports.keypair import KEYPAIR_REPORT
from ai.backend.manager.repositories.export.reports.project import PROJECT_REPORT
from ai.backend.manager.repositories.export.reports.session import SESSION_REPORT
from ai.backend.manager.repositories.export.reports.user import USER_REPORT


class ExportReportRegistry:
    """Registry for export report definitions.

    Manages a collection of ReportDef instances that can be
    looked up by their report_key.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._reports: dict[str, ReportDef] = {}

    def register(self, report: ReportDef) -> None:
        """Register a report definition.

        Args:
            report: The ReportDef to register
        """
        self._reports[report.report_key] = report

    def get(self, report_key: str) -> ReportDef | None:
        """Get ReportDef by report_key.

        Args:
            report_key: The unique identifier for the report

        Returns:
            ReportDef if found, None otherwise
        """
        return self._reports.get(report_key)

    def list_all(self) -> list[ReportDef]:
        """Return all registered reports.

        Returns:
            List of all ReportDef instances
        """
        return list(self._reports.values())

    @classmethod
    def create_default(cls) -> ExportReportRegistry:
        """Create the default export report registry with built-in reports.

        Returns:
            ExportReportRegistry with all built-in reports registered
        """
        registry = cls()
        registry.register(AUDIT_LOG_REPORT)
        registry.register(KEYPAIR_REPORT)
        registry.register(PROJECT_REPORT)
        registry.register(SESSION_REPORT)
        registry.register(USER_REPORT)
        return registry
