"""Lookup specs for the kernels table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Row

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.specs.lookup import FieldOwnerKeyLookup, FieldOwnerLookup


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


@dataclass
class KernelOwnerLookup(FieldOwnerLookup[KernelID, SessionID]):
    """Reads the session each of several kernels runs under.

    The batch counterpart of :class:`KernelSessionLookup`: it selects the pair, so which
    kernel each session answers for survives.
    """

    @override
    def build_query(self, field_ids: Sequence[KernelID]) -> sa.sql.Select[Any]:
        return sa.select(KernelRow.id, KernelRow.session_id).where(KernelRow.id.in_(field_ids))

    @override
    def to_entity_id(self, row: Row[Any]) -> SessionID:
        return SessionID(row[1])
