from __future__ import annotations

from uuid import UUID

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.login_client_type.db_source import (
    LoginClientTypeDBSource,
)

__all__ = ("LoginClientTypeRepository",)


class LoginClientTypeRepository:
    _db_source: LoginClientTypeDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = LoginClientTypeDBSource(db)

    async def create(self, name: str, description: str | None) -> LoginClientTypeData:
        return await self._db_source.create(name, description)

    async def get_by_id(self, type_id: UUID) -> LoginClientTypeData:
        return await self._db_source.get_by_id(type_id)

    async def get_by_name(self, name: str) -> LoginClientTypeData:
        return await self._db_source.get_by_name(name)

    async def list_all(self) -> list[LoginClientTypeData]:
        return await self._db_source.list_all()

    async def update(
        self,
        type_id: UUID,
        *,
        name: str | None,
        description_set: bool,
        description: str | None,
    ) -> LoginClientTypeData:
        return await self._db_source.update(
            type_id,
            name=name,
            description_set=description_set,
            description=description,
        )

    async def delete(self, type_id: UUID) -> LoginClientTypeData:
        return await self._db_source.delete(type_id)
