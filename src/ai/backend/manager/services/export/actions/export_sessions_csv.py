"""Action to export session data as CSV."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.repositories.base.export import StreamingExportQuery

from .base import ExportAction


@dataclass
class ExportSessionsCSVAction(ExportAction):
    """Action to export session data as CSV.

    Contains the pre-built query from adapter and export parameters.
    """

    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None  # Optional filename from header

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "export_sessions_csv"

    @override
    def entity_id(self) -> str | None:
        return "sessions"


@dataclass
class ExportSessionsCSVActionResult(BaseActionResult):
    """Result of session CSV export action.

    Contains an async iterator that yields row partitions.
    """

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str  # Generated or provided filename

    @override
    def entity_id(self) -> str | None:
        return "sessions"
