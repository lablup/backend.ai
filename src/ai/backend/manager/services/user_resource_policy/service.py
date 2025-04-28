import logging

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.exceptions import ObjectNotFound
from ai.backend.manager.models.resource_policy import (
    UserResourcePolicyRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.user_resource_policy.actions.create_user_resource_policy import (
    CreateUserResourcePolicyAction,
    CreateUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.actions.delete_user_resource_policy import (
    DeleteUserResourcePolicyAction,
    DeleteUserResourcePolicyActionResult,
)
from ai.backend.manager.services.user_resource_policy.actions.modify_user_resource_policy import (
    ModifyUserResourcePolicyAction,
    ModifyUserResourcePolicyActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserResourcePolicyService:
    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db = db

    async def create_user_resource_policy(
        self, action: CreateUserResourcePolicyAction
    ) -> CreateUserResourcePolicyActionResult:
        creator = action.creator
        to_create = creator.fields_to_store()

        async with self._db.begin_session() as db_sess:
            db_row = UserResourcePolicyRow(**to_create)
            db_sess.add(db_row)
            await db_sess.flush()
            result = db_row.to_dataclass()

        return CreateUserResourcePolicyActionResult(user_resource_policy=result)

    async def modify_user_resource_policy(
        self, action: ModifyUserResourcePolicyAction
    ) -> ModifyUserResourcePolicyActionResult:
        name = action.name
        modifier = action.modifier

        async with self._db.begin_session() as db_sess:
            query = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
            db_row = (await db_sess.execute(query)).scalar_one_or_none()
            if db_row is None:
                raise ObjectNotFound(f"User resource policy with name {name} not found.")
            to_update = modifier.fields_to_update()
            for key, value in to_update.items():
                setattr(db_row, key, value)

        return ModifyUserResourcePolicyActionResult(user_resource_policy=db_row.to_dataclass())

    async def delete_user_resource_policy(
        self, action: DeleteUserResourcePolicyAction
    ) -> DeleteUserResourcePolicyActionResult:
        name = action.name

        async with self._db.begin_session() as db_sess:
            query = sa.select(UserResourcePolicyRow).where(UserResourcePolicyRow.name == name)
            db_row = (await db_sess.execute(query)).scalar_one_or_none()
            if not db_row:
                raise ObjectNotFound(f"User resource policy with name {name} not found.")
            await db_sess.delete(db_row)

        return DeleteUserResourcePolicyActionResult(user_resource_policy=db_row.to_dataclass())
