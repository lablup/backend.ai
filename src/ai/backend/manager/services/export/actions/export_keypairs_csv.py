"""Action to export keypair data as CSV."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.repositories.base.export import StreamingExportQuery
from ai.backend.manager.services.export.actions.base import ExportAction


@dataclass(frozen=True)
class ExportKeypairsCSVAction(ExportAction):
    """Action to export keypair data as CSV.

    Contains the pre-built query from adapter and export parameters.
    """

    query: StreamingExportQuery
    encoding: str = "utf-8"
    filename: str | None = None  # Optional filename from header

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "export_keypairs_c_s_v"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class ExportKeypairsCSVActionResult:
    """Result of keypair CSV export action.

    Contains an async iterator that yields row partitions.
    """

    field_names: list[str]
    row_iterator: AsyncIterator[Sequence[Sequence[Any]]]
    encoding: str
    filename: str  # Generated or provided filename
