"""Export repository for data access operations.

This module provides the ExportRepository class that wraps
the export registry and db source.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

from ai.backend.manager.errors.export import ExportReportNotFound
from ai.backend.manager.repositories.base.export import ReportDef, StreamingExportQuery

from .db_source import ExportDBSource
from .registry import ExportReportRegistry


class ExportRepository:
    """Repository for export operations.

    Provides methods to access report definitions and execute
    streaming exports against the database.
    """

    def __init__(
        self,
        db_source: ExportDBSource,
        registry: ExportReportRegistry,
    ) -> None:
        """Initialize ExportRepository.

        Args:
            db_source: DB source for export operations
            registry: Export report registry
        """
        self._db_source = db_source
        self._registry = registry

    def get_report(self, report_key: str) -> ReportDef:
        """Get ReportDef by report_key.

        Args:
            report_key: The unique identifier for the report

        Returns:
            ReportDef for the requested report

        Raises:
            ExportReportNotFound: If report_key is not found
        """
        report = self._registry.get(report_key)
        if report is None:
            raise ExportReportNotFound(report_key)
        return report

    def list_reports(self) -> list[ReportDef]:
        """List all available reports.

        Returns:
            List of all registered ReportDef instances
        """
        return self._registry.list_all()

    async def execute_export(
        self,
        query: StreamingExportQuery,
    ) -> AsyncIterator[Sequence[Sequence[Any]]]:
        """Execute streaming export.

        Args:
            query: Export query containing fields, conditions, orders, and limits

        Yields:
            Partitions of row values (each row in query.fields order)
        """
        async for partition in self._db_source.stream_export(query):
            yield partition
