from typing import Any, Mapping

import sqlalchemy as sa

from ai.backend.manager.errors.exceptions import ObjectNotFound
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class KeypairResourcePolicyRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create(self, fields: Mapping[str, Any]) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            db_row = KeyPairResourcePolicyRow(**fields)
            db_sess.add(db_row)
            await db_sess.flush()
            return db_row.to_dataclass()

    async def get_by_name(self, name: str) -> KeyPairResourcePolicyData:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"Keypair resource policy with name {name} not found.")
            return row.to_dataclass()

    async def update(self, name: str, fields: Mapping[str, Any]) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"Keypair resource policy with name {name} not found.")
            for key, value in fields.items():
                setattr(row, key, value)
            await db_sess.flush()
            return row.to_dataclass()

    async def delete(self, name: str) -> KeyPairResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            query = sa.select(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"Keypair resource policy with name {name} not found.")
            await db_sess.delete(row)
            return row.to_dataclass()
