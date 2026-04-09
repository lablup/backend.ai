from __future__ import annotations

from typing import cast
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.errors.auth import LoginClientTypeNotFound
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater, execute_updater

__all__ = ("LoginClientTypeDBSource",)


class LoginClientTypeDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(
        self,
        creator: Creator[LoginClientTypeRow],
    ) -> LoginClientTypeData:
        async with self._db.begin_session() as session:
            result = await execute_creator(session, creator)
            return result.row.to_dataclass()

    async def get_by_id(self, type_id: UUID) -> LoginClientTypeData:
        async with self._db.begin_readonly_session() as session:
            row = cast(
                LoginClientTypeRow | None,
                await session.scalar(
                    sa.select(LoginClientTypeRow).where(LoginClientTypeRow.id == type_id)
                ),
            )
            if row is None:
                raise LoginClientTypeNotFound(
                    extra_msg=f"Login client type with id {type_id} not found."
                )
            return row.to_dataclass()

    async def get_by_name(self, name: str) -> LoginClientTypeData:
        async with self._db.begin_readonly_session() as session:
            row = cast(
                LoginClientTypeRow | None,
                await session.scalar(
                    sa.select(LoginClientTypeRow).where(LoginClientTypeRow.name == name)
                ),
            )
            if row is None:
                raise LoginClientTypeNotFound(
                    extra_msg=f"Login client type with name '{name}' not found."
                )
            return row.to_dataclass()

    async def update(
        self,
        updater: Updater[LoginClientTypeRow],
    ) -> LoginClientTypeData:
        async with self._db.begin_session() as session:
            result = await execute_updater(session, updater)
            if result is None:
                raise LoginClientTypeNotFound(
                    extra_msg=f"Login client type with id {updater.pk_value} not found."
                )
            return result.row.to_dataclass()

    async def delete(self, type_id: UUID) -> LoginClientTypeData:
        async with self._db.begin_session() as session:
            row = cast(
                LoginClientTypeRow | None,
                await session.scalar(
                    sa.select(LoginClientTypeRow).where(LoginClientTypeRow.id == type_id)
                ),
            )
            if row is None:
                raise LoginClientTypeNotFound(
                    extra_msg=f"Login client type with id {type_id} not found."
                )
            data = row.to_dataclass()
            await session.delete(row)
            return data
