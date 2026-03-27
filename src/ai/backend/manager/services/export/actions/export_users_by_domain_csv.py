"""Action to export user data scoped to a domain."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import StreamingExportQuery

from .base import ExportAction


@dataclass
class ExportUsersByDomainCSVAction(ExportAction):
    """Export user CSV scoped to a specific domain."""

    domain_name: str
    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return f"users:domain:{self.domain_name}"


@dataclass
class ExportUsersByDomainCSVActionResult(BaseActionResult):
    """Result of domain-scoped user CSV export action."""

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str

    @override
    def entity_id(self) -> str | None:
        return "users"
