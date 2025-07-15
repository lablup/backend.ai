from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.errors.exceptions import ObjectNotFound
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class KeypairResourcePolicyRepository:
    def __init__(self, db: ExtendedAsyncSAEngine):
        self._db = db

    async def create_keypair_resource_policy(self, fields: dict) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            return await self._create(db_sess, fields)

    async def get_keypair_resource_policy_by_name(self, name: str) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_by_name(db_sess, name)
            if row is None:
                raise ObjectNotFound(object_name="KeyPairResourcePolicy", search_key=name)
            return row.to_dataclass()

    async def update_keypair_resource_policy(
        self, name: str, fields: dict
    ) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_by_name(db_sess, name)
            if row is None:
                raise ObjectNotFound(object_name="KeyPairResourcePolicy", search_key=name)
            return await self._update(db_sess, row, fields)

    async def delete_keypair_resource_policy(self, name: str) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_by_name(db_sess, name)
            if row is None:
                raise ObjectNotFound(object_name="KeyPairResourcePolicy", search_key=name)
            data = row.to_dataclass()
            await db_sess.delete(row)
            return data

    async def _get_by_name(
        self, session: SASession, name: str
    ) -> Optional[KeyPairResourcePolicyRow]:
        stmt = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _create(self, session: SASession, fields: dict) -> KeyPairResourcePolicyData:
        row = KeyPairResourcePolicyRow(**fields)
        session.add(row)
        await session.flush()
        return row.to_dataclass()

    async def _update(
        self, session: SASession, row: KeyPairResourcePolicyRow, fields: dict
    ) -> KeyPairResourcePolicyData:
        for key, value in fields.items():
            setattr(row, key, value)
        await session.flush()
        return row.to_dataclass()


class ProjectResourcePolicyRepository:
    def __init__(self, db: ExtendedAsyncSAEngine):
        self._db = db

    async def create_project_resource_policy(self, fields: dict) -> ProjectResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            return await self._create(db_sess, fields)

    async def get_project_resource_policy_by_name(self, name: str) -> ProjectResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_by_name(db_sess, name)
            if row is None:
                raise ObjectNotFound(object_name="ProjectResourcePolicy", search_key=name)
            return row.to_dataclass()

    async def update_project_resource_policy(
        self, name: str, fields: dict
    ) -> ProjectResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_by_name(db_sess, name)
            if row is None:
                raise ObjectNotFound(object_name="ProjectResourcePolicy", search_key=name)
            return await self._update(db_sess, row, fields)

    async def delete_project_resource_policy(self, name: str) -> ProjectResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_by_name(db_sess, name)
            if row is None:
                raise ObjectNotFound(object_name="ProjectResourcePolicy", search_key=name)
            data = row.to_dataclass()
            await db_sess.delete(row)
            return data

    async def _get_by_name(
        self, session: SASession, name: str
    ) -> Optional[ProjectResourcePolicyRow]:
        stmt = sa.select(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == name)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _create(self, session: SASession, fields: dict) -> ProjectResourcePolicyData:
        row = ProjectResourcePolicyRow(**fields)
        session.add(row)
        await session.flush()
        return row.to_dataclass()

    async def _update(
        self, session: SASession, row: ProjectResourcePolicyRow, fields: dict
    ) -> ProjectResourcePolicyData:
        for key, value in fields.items():
            setattr(row, key, value)
        await session.flush()
        return row.to_dataclass()


class UserResourcePolicyRepository:
    def __init__(self, db: ExtendedAsyncSAEngine):
        self._db = db

    async def create_user_resource_policy(self, fields: dict) -> UserResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            return await self._create(db_sess, fields)

    async def get_user_resource_policy_by_name(self, name: str) -> UserResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_by_name(db_sess, name)
            if row is None:
                raise ObjectNotFound(object_name="UserResourcePolicy", search_key=name)
            return row.to_dataclass()

    async def update_user_resource_policy(self, name: str, fields: dict) -> UserResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_by_name(db_sess, name)
            if row is None:
                raise ObjectNotFound(object_name="UserResourcePolicy", search_key=name)
            return await self._update(db_sess, row, fields)

    async def delete_user_resource_policy(self, name: str) -> UserResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            row = await self._get_by_name(db_sess, name)
            if row is None:
                raise ObjectNotFound(object_name="UserResourcePolicy", search_key=name)
            data = row.to_dataclass()
            await db_sess.delete(row)
            return data

    async def _get_by_name(self, session: SASession, name: str) -> Optional[UserResourcePolicyRow]:
        stmt = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _create(self, session: SASession, fields: dict) -> UserResourcePolicyData:
        row = UserResourcePolicyRow(**fields)
        session.add(row)
        await session.flush()
        return row.to_dataclass()

    async def _update(
        self, session: SASession, row: UserResourcePolicyRow, fields: dict
    ) -> UserResourcePolicyData:
        for key, value in fields.items():
            setattr(row, key, value)
        await session.flush()
        return row.to_dataclass()
