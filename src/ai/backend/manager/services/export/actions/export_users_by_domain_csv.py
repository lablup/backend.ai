"""Action to export user data scoped to a domain."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import StreamingExportQuery

from .base import ExportDomainScopeAction, ExportScopeActionResult


@dataclass
class ExportUsersByDomainCSVAction(ExportDomainScopeAction):
    """Export user CSV scoped to a specific domain."""

    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "export_users_by_domain_c_s_v"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ExportUsersByDomainCSVActionResult(ExportScopeActionResult):
    """Result of domain-scoped user CSV export action."""

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str
