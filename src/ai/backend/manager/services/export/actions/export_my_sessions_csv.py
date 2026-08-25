"""Action to export session data scoped to the current user."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import StreamingExportQuery

from .base import ExportScopeActionResult, ExportUserScopeAction


@dataclass
class ExportMySessionsCSVAction(ExportUserScopeAction):
    """Export session CSV scoped to the current user."""

    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "export_my_sessions_c_s_v"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ExportMySessionsCSVActionResult(ExportScopeActionResult):
    """Result of user-scoped session CSV export action."""

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str
