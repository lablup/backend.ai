import logging
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.engine.row import Row
from sqlalchemy.exc import SQLAlchemyError

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.exceptions import InternalServerError
from ai.backend.manager.models.group import association_groups_users, groups
from ai.backend.manager.models.user import UserRow, UserStatus, check_credential, users
from ai.backend.manager.models.utils import execute_with_retry

from .base import BaseAuthRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserRepository(BaseAuthRepository):
    async def check_user_in_group(self, group_id: str, user_id: str) -> Optional[Row]:
        try:
            query = (
                sa.select([association_groups_users.c.group_id])
                .select_from(association_groups_users)
                .where(
                    (association_groups_users.c.group_id == group_id)
                    & (association_groups_users.c.user_id == user_id),
                )
            )
            async with self._db.begin() as conn:
                result = await conn.execute(query)
                return result.first()
        except SQLAlchemyError as e:
            log.error("Failed to check user in group: {}", e)
            raise InternalServerError("Database error occurred while checking user group membership")

    async def check_email_exists(self, email: str) -> Optional[Row]:
        try:
            query = sa.select([users]).select_from(users).where((users.c.email == email))
            async with self._db.begin() as conn:
                result = await conn.execute(query)
                return result.first()
        except SQLAlchemyError as e:
            log.error("Failed to check email exists: {}", e)
            raise InternalServerError("Database error occurred while checking email existence")

    async def create_user(self, user_data: dict) -> Optional[Row]:
        async with self._db.begin() as conn:
            query = users.insert().values(user_data)
            result = await conn.execute(query)
            if result.rowcount > 0:
                checkq = users.select().where(users.c.email == user_data["email"])
                result = await conn.execute(checkq)
                return result.first()
            return None

    async def add_user_to_group(self, user_uuid: str, group_name: str, domain_name: str) -> None:
        async with self._db.begin() as conn:
            query = (
                sa.select([groups.c.id])
                .select_from(groups)
                .where(groups.c.domain_name == domain_name)
                .where(groups.c.name == group_name)
            )
            result = await conn.execute(query)
            grp = result.first()
            if grp is not None:
                values = [{"user_id": user_uuid, "group_id": grp.id}]
                query = association_groups_users.insert().values(values)
                await conn.execute(query)

    async def update_user_status(self, email: str, status: UserStatus) -> None:
        async with self._db.begin() as conn:
            query = users.update().values(status=status).where(users.c.email == email)
            await conn.execute(query)

    async def get_user_by_email_and_domain(self, email: str, domain_name: str) -> Optional[Row]:
        async with self._db.begin() as conn:
            query = (
                sa.select([users])
                .select_from(users)
                .where(
                    (users.c.email == email) & (users.c.domain_name == domain_name),
                )
            )
            result = await conn.execute(query)
            return result.first()

    async def update_user_full_name(self, email: str, full_name: str) -> None:
        async with self._db.begin() as conn:
            data = {"full_name": full_name}
            update_query = users.update().values(data).where(users.c.email == email)
            await conn.execute(update_query)

    async def update_user_password(self, email: str, password: str) -> None:
        async with self._db.begin() as conn:
            data = {
                "password": password,
                "need_password_change": False,
                "password_changed_at": sa.func.now(),
            }
            query = users.update().values(data).where(users.c.email == email)
            await conn.execute(query)

    async def update_user_password_by_uuid(self, user_uuid: str, password: str) -> datetime:
        async def _update() -> datetime:
            async with self._db.begin() as conn:
                data = {
                    "password": password,
                    "need_password_change": False,
                    "password_changed_at": sa.func.now(),
                }
                query = (
                    sa.update(users)
                    .values(data)
                    .where(users.c.uuid == user_uuid)
                    .returning(users.c.password_changed_at)
                )
                result = await conn.execute(query)
                return result.scalar()

        return await execute_with_retry(_update)

    async def get_current_datetime(self) -> datetime:
        async with self._db.begin_readonly() as db_conn:
            return await db_conn.scalar(sa.select(sa.func.now()))

    async def check_user_credential(self, domain: str, email: str, password: str) -> Optional[Row]:
        return await check_credential(
            db=self._db,
            domain=domain,
            email=email,
            password=password,
        )

    async def get_user_row_by_uuid(self, user_uuid: str) -> Optional[UserRow]:
        async with self._db.begin_session() as db_session:
            return await UserRow.query_user_by_uuid(user_uuid, db_session)