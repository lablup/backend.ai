from typing import Any, Mapping

import sqlalchemy as sa

from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for user_resource_policy repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.USER_RESOURCE_POLICY)


class UserResourcePolicyRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def create(self, fields: Mapping[str, Any]) -> UserResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            db_row = UserResourcePolicyRow(**fields)
            db_sess.add(db_row)
            await db_sess.flush()
            return db_row.to_dataclass()

    @repository_decorator()
    async def get_by_name(self, name: str) -> UserResourcePolicyData:
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"User resource policy with name {name} not found.")
            return row.to_dataclass()

    @repository_decorator()
    async def update(self, name: str, fields: Mapping[str, Any]) -> UserResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            query = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"User resource policy with name {name} not found.")
            for key, value in fields.items():
                setattr(row, key, value)
            await db_sess.flush()
            return row.to_dataclass()

    @repository_decorator()
    async def delete(self, name: str) -> UserResourcePolicyData:
        async with self._db.begin_session() as db_sess:
            query = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise ObjectNotFound(f"User resource policy with name {name} not found.")
            await db_sess.delete(row)
            return row.to_dataclass()
