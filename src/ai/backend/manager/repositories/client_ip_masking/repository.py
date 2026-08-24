from __future__ import annotations

from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .db_source.db_source import ClientIPMaskingDBSource


class ClientIPMaskingRepository:
    """The read other domains resolve their masking through; the writes run against ops."""

    _db_source: ClientIPMaskingDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ClientIPMaskingDBSource(db)

    async def resolve_mode(self, target_type: ClientIPMaskingTarget) -> ClientIPMaskingMode:
        return await self._db_source.resolve_mode(target_type)
