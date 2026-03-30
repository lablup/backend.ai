"""Action to export session data scoped to a project."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import StreamingExportQuery

from .base import ExportAction


@dataclass
class ExportSessionsByProjectCSVAction(ExportAction):
    """Export session CSV scoped to a specific project."""

    project_id: UUID
    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return f"sessions:project:{self.project_id}"


@dataclass
class ExportSessionsByProjectCSVActionResult(BaseActionResult):
    """Result of project-scoped session CSV export action."""

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str

    @override
    def entity_id(self) -> str | None:
        return "sessions"
