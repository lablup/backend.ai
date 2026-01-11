"""Export service for CSV streaming export.

This module provides the ExportService class that orchestrates
CSV export operations with concurrency control.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from typing import Any

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.export import (
    InvalidExportFieldKeys,
    TooManyConcurrentExports,
)
from ai.backend.manager.repositories.base.export import (
    ExportDataStream,
    StreamingExportQuery,
)
from ai.backend.manager.repositories.export.repository import ExportRepository
from ai.backend.manager.services.export.actions.export_csv import (
    ExportCsvAction,
    ExportCsvActionResult,
)
from ai.backend.manager.services.export.actions.list_reports import (
    ListReportsAction,
    ListReportsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class ExportService:
    """CSV Export service.

    Provides action-based methods for listing available reports and executing
    CSV exports with concurrency control via semaphore.
    """

    _export_repository: ExportRepository

    def __init__(
        self,
        export_repository: ExportRepository,
        max_concurrent_exports: int,
    ) -> None:
        """Initialize ExportService.

        Args:
            export_repository: Repository for export operations
            max_concurrent_exports: Maximum number of concurrent export operations
        """
        self._export_repository = export_repository
        self._semaphore = asyncio.Semaphore(max_concurrent_exports)

    async def list_reports(self, action: ListReportsAction) -> ListReportsActionResult:
        """List all available export reports.

        Args:
            action: List reports action

        Returns:
            ListReportsActionResult containing all registered reports
        """
        log.info("Listing available export reports")
        reports = self._export_repository.list_reports()
        return ListReportsActionResult(reports=reports)

    async def export_csv(self, action: ExportCsvAction) -> ExportCsvActionResult:
        """Export report to CSV.

        Args:
            action: Export CSV action containing report_key, query_params, field_keys, and filename

        Returns:
            ExportCsvActionResult containing the CSV streaming reader

        Raises:
            ExportReportNotFound: If report_key is not found
            InvalidExportFieldKeys: If any field_keys are invalid
            TooManyConcurrentExports: Concurrent export limit exceeded
        """
        log.info("Starting CSV export for report: {}", action.report_key)

        # Get report (raises ExportReportNotFound if not found)
        report = self._export_repository.get_report(action.report_key)

        # Validate field keys
        invalid_keys = report.validate_field_keys(action.field_keys)
        if invalid_keys:
            raise InvalidExportFieldKeys(invalid_keys)

        # Get selected field definitions and build query
        fields = report.get_fields_by_keys(action.field_keys)
        query = StreamingExportQuery.from_params(action.query_params, report.select_from, fields)

        # Check concurrent export limit (non-blocking)
        if self._semaphore.locked():
            raise TooManyConcurrentExports()

        # Extract field names for header
        field_names = [f.name for f in fields]

        data_stream = ExportDataStream(
            field_names=field_names,
            reader=self._stream_row_values(query),
        )

        return ExportCsvActionResult(data_stream=data_stream)

    async def _stream_row_values(
        self,
        query: StreamingExportQuery,
    ) -> AsyncIterator[Sequence[Sequence[Any]]]:
        """Stream row values with semaphore limiting concurrent exports.

        Yields partitions of row values for efficient async processing.

        Args:
            query: Export query containing fields, conditions, and limits

        Yields:
            Partitions of row values (each row in query.fields order)
        """
        async with self._semaphore:
            async for partition in self._export_repository.execute_export(query):
                yield partition
