from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import GlobalEntityIDCache
from ai.backend.manager.errors.permission import GlobalEntityMissing
from ai.backend.manager.models.global_entity.row import GlobalEntityRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

__all__ = ("GlobalEntityIDLoader",)

_RECOVERY_COMMAND = "backend.ai mgr permissions provision"


class GlobalEntityIDLoader:
    """Reads the global entities that have a virtual entity and fills the id cache."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def load(self) -> None:
        query = sa.select(GlobalEntityRow.name, GlobalEntityRow.id).join(
            VirtualEntityRow,
            sa.and_(
                VirtualEntityRow.entity_type == GlobalEntityType.name(),
                VirtualEntityRow.entity_id == GlobalEntityRow.id,
            ),
        )
        async with self._db.begin_readonly_session_read_committed() as session:
            rows = (await session.execute(query)).all()
        ids = {GlobalEntityName(row.name): GlobalEntityID(row.id) for row in rows}
        missing = [name for name in GlobalEntityName if name not in ids]
        if missing:
            raise GlobalEntityMissing(
                f"The global entities {', '.join(missing)} or their virtual entities do not"
                f" exist. Run `{_RECOVERY_COMMAND}` and restart the manager."
            )
        GlobalEntityIDCache.fill(ids)
