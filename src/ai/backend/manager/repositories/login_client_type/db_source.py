from __future__ import annotations

from typing import cast
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.data.login_client_type.types import (
    LoginClientTypeData,
    LoginClientTypeSearchResult,
)
from ai.backend.manager.errors.auth import LoginClientTypeNotFound
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
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

    async def get_by_id(self, login_client_type_id: UUID) -> LoginClientTypeData:
        async with self._db.begin_readonly_session() as session:
            row = cast(
                LoginClientTypeRow | None,
                await session.scalar(
                    sa.select(LoginClientTypeRow).where(
                        LoginClientTypeRow.id == login_client_type_id
                    )
                ),
            )
            if row is None:
                raise LoginClientTypeNotFound(
                    extra_msg=f"Login client type with id {login_client_type_id} not found."
                )
            return row.to_dataclass()

    async def search(self, querier: BatchQuerier) -> LoginClientTypeSearchResult:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(LoginClientTypeRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [row.LoginClientTypeRow.to_dataclass() for row in result.rows]
            return LoginClientTypeSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

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

    async def delete(self, login_client_type_id: UUID) -> LoginClientTypeData:
        async with self._db.begin_session() as session:
            row = cast(
                LoginClientTypeRow | None,
                await session.scalar(
                    sa.select(LoginClientTypeRow).where(
                        LoginClientTypeRow.id == login_client_type_id
                    )
                ),
            )
            if row is None:
                raise LoginClientTypeNotFound(
                    extra_msg=f"Login client type with id {login_client_type_id} not found."
                )
            data = row.to_dataclass()
            await session.delete(row)
            return data
