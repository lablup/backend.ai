"""Update specs for kernel rows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.types import KernelId
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.kernel.searchable_fields import KernelSearchableFields
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater

__all__ = ("KernelSessionNameBatchUpdater",)


@dataclass
class KernelSessionNameBatchUpdater(DataBatchUpdater[KernelRow, KernelId]):
    """Copy a session's new name onto every kernel of the session."""

    session_id: SessionID
    session_name: str

    @property
    @override
    def row_class(self) -> type[KernelRow]:
        return KernelRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [
            KernelSearchableFields.own.session_id.filter.equals(
                UUIDEqualMatchSpec(value=self.session_id, negated=False)
            )
        ]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"session_name": self.session_name}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: KernelRow) -> KernelId:
        return KernelId(row.id)
