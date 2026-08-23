"""Database source for runtime variant preset repository operations."""

from __future__ import annotations

import logging
from uuid import UUID

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.errors.resource import RuntimeVariantPresetNotFound
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantPresetDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_by_id(self, preset_id: UUID) -> RuntimeVariantPresetData:
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(RuntimeVariantPresetRow).where(RuntimeVariantPresetRow.id == preset_id)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                raise RuntimeVariantPresetNotFound()
            return row.to_data()

    async def get_by_ids(self, preset_ids: list[UUID]) -> list[RuntimeVariantPresetData]:
        if not preset_ids:
            return []
        async with self._db.begin_readonly_session_read_committed() as session:
            stmt = sa.select(RuntimeVariantPresetRow).where(
                RuntimeVariantPresetRow.id.in_(preset_ids)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [row.to_data() for row in rows]
