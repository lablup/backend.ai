"""Action to export session data scoped to the current user."""

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
class ExportMySessionsCSVAction(ExportAction):
    """Export session CSV scoped to the current user."""

    user_uuid: UUID
    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return f"sessions:user:{self.user_uuid}"


@dataclass
class ExportMySessionsCSVActionResult(BaseActionResult):
    """Result of user-scoped session CSV export action."""

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str

    @override
    def entity_id(self) -> str | None:
        return "sessions"
