from __future__ import annotations

from uuid import UUID

from ai.backend.manager.data.login_client_type.types import (
    LoginClientTypeData,
    LoginClientTypeSearchResult,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.login_client_type.db_source import (
    LoginClientTypeDBSource,
)

__all__ = ("LoginClientTypeRepository",)


class LoginClientTypeRepository:
    _db_source: LoginClientTypeDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = LoginClientTypeDBSource(db)

    async def get_by_id(self, login_client_type_id: UUID) -> LoginClientTypeData:
        return await self._db_source.get_by_id(login_client_type_id)

    async def search(self, querier: BatchQuerier) -> LoginClientTypeSearchResult:
        return await self._db_source.search(querier)
