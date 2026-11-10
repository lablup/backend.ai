"""Action to export keypair data scoped to the current user."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import StreamingExportQuery
from ai.backend.manager.services.export.actions.base import (
    ExportScopeActionResult,
    ExportUserScopeAction,
)


@dataclass(frozen=True)
class ExportMyKeypairsCSVAction(ExportUserScopeAction):
    """Export keypair CSV scoped to the current user."""

    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "export_my_keypairs_c_s_v"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class ExportMyKeypairsCSVActionResult(ExportScopeActionResult):
    """Result of user-scoped keypair CSV export action."""

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str
