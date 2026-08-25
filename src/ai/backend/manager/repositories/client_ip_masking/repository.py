from __future__ import annotations

from ai.backend.manager.data.client_ip.masking import ClientIPMasker, ClientIPMaskingTarget
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .db_source.db_source import ClientIPMaskingDBSource


class ClientIPMaskingRepository:
    """The read other domains resolve their masking through; the writes run against ops."""

    _db_source: ClientIPMaskingDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ClientIPMaskingDBSource(db)

    async def resolve_masker(self, target_type: ClientIPMaskingTarget) -> ClientIPMasker:
        return await self._db_source.resolve_masker(target_type)

    async def mask(self, target_type: ClientIPMaskingTarget, client_ip: str | None) -> str | None:
        """The address a record of this target keeps.

        The single place masking is applied: every record type resolves its own
        policy here rather than repeating the two steps at each write.
        """
        masker = await self.resolve_masker(target_type)
        return masker.mask(client_ip)
