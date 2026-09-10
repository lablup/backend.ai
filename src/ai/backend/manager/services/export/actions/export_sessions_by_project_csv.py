"""Action to export session data scoped to a project."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import StreamingExportQuery
from ai.backend.manager.services.export.actions.base import (
    ExportProjectScopeAction,
    ExportScopeActionResult,
)


@dataclass(frozen=True)
class ExportSessionsByProjectCSVAction(ExportProjectScopeAction):
    """Export session CSV scoped to a specific project."""

    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "export_sessions_by_project_c_s_v"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class ExportSessionsByProjectCSVActionResult(ExportScopeActionResult):
    """Result of project-scoped session CSV export action."""

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str
