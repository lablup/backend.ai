"""Action to export user data as CSV."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.repositories.base.export import StreamingExportQuery

from .base import ExportAction


@dataclass
class ExportUsersCSVAction(ExportAction):
    """Action to export user data as CSV.

    Contains the pre-built query from adapter and export parameters.
    """

    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None  # Optional filename from header

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "export_users_csv"

    @override
    def entity_id(self) -> Optional[str]:
        return "users"


@dataclass
class ExportUsersCSVActionResult(BaseActionResult):
    """Result of user CSV export action.

    Contains an async iterator that yields row partitions.
    """

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str  # Generated or provided filename

    @override
    def entity_id(self) -> Optional[str]:
        return "users"
