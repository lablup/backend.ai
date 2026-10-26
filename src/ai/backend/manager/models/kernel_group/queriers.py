from __future__ import annotations

from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.data.kernel_group.types import KernelGroupData
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier, OwnedFieldQuerier


class BulkKernelGroupQuerier(BulkFieldQuerier[KernelGroupRow, KernelGroupData]):
    """The kernel groups the caller named."""

    @override
    def row_class(self) -> type[KernelGroupRow]:
        return KernelGroupRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KernelGroupRow.id

    @override
    def to_data(self, row: KernelGroupRow) -> KernelGroupData:
        return row.to_data()


class MainKernelGroupQuerier(OwnedFieldQuerier[SessionID, KernelGroupRow, KernelGroupData]):
    """The main kernel group of a session.

    The unique ``(session_id, role)`` constraint caps the main role at one per session.
    """

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelGroupRow).where(KernelGroupRow.role == DEFAULT_ROLE)

    @override
    def owner_id_column(self) -> InstrumentedAttribute[Any]:
        return KernelGroupRow.session_id

    @override
    def to_data(self, row: KernelGroupRow) -> KernelGroupData:
        return row.to_data()
