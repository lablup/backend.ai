"""Lookup specs for the kernels table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.specs.lookup import FieldOwnerKeyLookup


@dataclass
class KernelSessionLookup(FieldOwnerKeyLookup[SessionID]):
    """Reads the session a kernel runs under.

    Keyed by the kernel id a request carries rather than by an allocation row's id:
    what a caller names is the kernel, and the session is what answers for it.
    """

    kernel_id: KernelID

    @override
    def build_query(self) -> sa.sql.Select[Any]:
        return sa.select(KernelRow.session_id).where(KernelRow.id == self.kernel_id)

    @override
    def to_entity_id(self, value: UUID) -> SessionID:
        return SessionID(value)
