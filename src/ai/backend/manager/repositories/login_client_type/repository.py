from __future__ import annotations

from uuid import UUID

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.login_client_type.db_source import (
    LoginClientTypeDBSource,
)

__all__ = ("LoginClientTypeRepository",)


class LoginClientTypeRepository:
    _db_source: LoginClientTypeDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = LoginClientTypeDBSource(db)

    async def create(self, creator: Creator[LoginClientTypeRow]) -> LoginClientTypeData:
        return await self._db_source.create(creator)

    async def get_by_id(self, type_id: UUID) -> LoginClientTypeData:
        return await self._db_source.get_by_id(type_id)

    async def get_by_name(self, name: str) -> LoginClientTypeData:
        return await self._db_source.get_by_name(name)

    async def update(self, updater: Updater[LoginClientTypeRow]) -> LoginClientTypeData:
        return await self._db_source.update(updater)

    async def delete(self, type_id: UUID) -> LoginClientTypeData:
        return await self._db_source.delete(type_id)
