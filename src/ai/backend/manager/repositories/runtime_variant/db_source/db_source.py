"""Database source for runtime variant repository operations."""

from __future__ import annotations

import logging
from uuid import UUID

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.errors.resource import RuntimeVariantNotFound
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_by_id(self, variant_id: UUID) -> RuntimeVariantData:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(RuntimeVariantRow).where(RuntimeVariantRow.id == variant_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise RuntimeVariantNotFound()
            return row.to_data()

    async def get_by_name(self, name: str) -> RuntimeVariantData:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(RuntimeVariantRow).where(RuntimeVariantRow.name == name)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise RuntimeVariantNotFound()
            return row.to_data()
