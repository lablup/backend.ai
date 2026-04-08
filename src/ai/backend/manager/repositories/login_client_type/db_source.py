from __future__ import annotations

from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.errors.auth import LoginClientTypeConflict, LoginClientTypeNotFound
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("LoginClientTypeDBSource",)


class LoginClientTypeDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(self, name: str, description: str | None) -> LoginClientTypeData:
        async with self._db.begin_session() as session:
            row = LoginClientTypeRow()
            row.name = name
            row.description = description
            session.add(row)
            try:
                await session.flush()
            except IntegrityError as e:
                raise LoginClientTypeConflict(
                    f"Login client type with name '{name}' already exists."
                ) from e
            await session.refresh(row)
            return row.to_dataclass()

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

    async def list_all(self) -> list[LoginClientTypeData]:
        async with self._db.begin_readonly_session() as session:
            result = await session.scalars(
                sa.select(LoginClientTypeRow).order_by(LoginClientTypeRow.name)
            )
            return [row.to_dataclass() for row in result.all()]

    async def update(
        self,
        type_id: UUID,
        *,
        name: str | None,
        description_set: bool,
        description: str | None,
    ) -> LoginClientTypeData:
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
            if name is not None:
                row.name = name
            if description_set:
                row.description = description
            try:
                await session.flush()
            except IntegrityError as e:
                raise LoginClientTypeConflict(
                    f"Login client type with name '{name}' already exists."
                ) from e
            await session.refresh(row)
            return row.to_dataclass()

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
