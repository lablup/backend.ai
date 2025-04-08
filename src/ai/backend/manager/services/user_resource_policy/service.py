import logging
from typing import Any

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.base import set_if_set
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
        name = action.name
        props = action.props

        async with self._db.begin_session() as db_sess:
            row = props.to_db_row(name)
            db_sess.add(row)
            await db_sess.flush()
        return CreateUserResourcePolicyActionResult(user_resource_policy=row)

    async def modify_user_resource_policy(
        self, action: ModifyUserResourcePolicyAction
    ) -> ModifyUserResourcePolicyActionResult:
        name = action.name
        props = action.props

        async with self._db.begin_session() as db_sess:
            data: dict[str, Any] = {}
            set_if_set(props, data, "max_vfolder_count")
            set_if_set(props, data, "max_quota_scope_size")
            set_if_set(props, data, "max_session_count_per_model_session")
            set_if_set(props, data, "max_customized_image_count")
            update_query = (
                sa.update(UserResourcePolicyRow)
                .values(data)
                .where(UserResourcePolicyRow.name == name)
                .returning(*UserResourcePolicyRow.__table__.c)
            )
            row = await db_sess.execute(update_query)

        return ModifyUserResourcePolicyActionResult(user_resource_policy=row)

    async def delete_user_resource_policy(
        self, action: DeleteUserResourcePolicyAction
    ) -> DeleteUserResourcePolicyActionResult:
        name = action.name

        async with self._db.begin_session() as db_sess:
            delete_query = (
                sa.delete(UserResourcePolicyRow)
                .where(UserResourcePolicyRow.name == name)
                .returning(*UserResourcePolicyRow.__table__.c)
            )
            row = await db_sess.execute(delete_query)

        return DeleteUserResourcePolicyActionResult(user_resource_policy=row)
