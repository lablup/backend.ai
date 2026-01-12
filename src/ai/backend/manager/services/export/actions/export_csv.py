"""Action for CSV export execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.repositories.base.export import ExportQueryParams

from .base import ExportAction

if TYPE_CHECKING:
    from ai.backend.manager.repositories.base.export import ExportDataStream


@dataclass
class ExportCsvAction(ExportAction):
    """Action to export a report to CSV format.

    Attributes:
        report_key: Report identifier to export
        query_params: Export query parameters (conditions, orders, max_rows, statement_timeout_sec)
        field_keys: List of field keys to include in export
    """

    report_key: str
    query_params: ExportQueryParams
    field_keys: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return self.report_key

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "export_csv"


@dataclass
class ExportCsvActionResult(BaseActionResult):
    """Result of CSV export action.

    Attributes:
        data_stream: Export data stream with field names and reader
    """

    data_stream: ExportDataStream

    @override
    def entity_id(self) -> Optional[str]:
        return None
