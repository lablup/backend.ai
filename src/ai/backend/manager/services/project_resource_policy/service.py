import logging
from typing import Any

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.base import set_if_set
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
    CreateProjectResourcePolicyActionResult,
)
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction,
    DeleteProjectResourcePolicyActionResult,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
    ModifyProjectResourcePolicyActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ProjectResourcePolicyService:
    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db = db

    async def create_project_resource_policy(
        self, action: CreateProjectResourcePolicyAction
    ) -> CreateProjectResourcePolicyActionResult:
        name = action.name
        props = action.props

        async with self._db.begin_session() as sess:
            row = ProjectResourcePolicyRow(
                name,
                props.max_vfolder_count,
                props.max_quota_scope_size,
                props.max_network_count,
            )
            sess.add(row)
            await sess.flush()

        return CreateProjectResourcePolicyActionResult(project_resource_policy=row)

    async def modify_project_resource_policy(
        self, action: ModifyProjectResourcePolicyAction
    ) -> ModifyProjectResourcePolicyActionResult:
        name = action.name
        props = action.props

        data: dict[str, Any] = {}
        set_if_set(props, data, "max_vfolder_count")
        set_if_set(props, data, "max_quota_scope_size")
        set_if_set(props, data, "max_network_count")

        async with self._db.begin_session() as db_sess:
            update_query = (
                sa.update(ProjectResourcePolicyRow)
                .values(data)
                .where(ProjectResourcePolicyRow.name == name)
                .returning(ProjectResourcePolicyRow.__table__.c)
            )
            result = await db_sess.execute(update_query)

        return ModifyProjectResourcePolicyActionResult(project_resource_policy=result)

    async def delete_project_resource_policy(
        self, action: DeleteProjectResourcePolicyAction
    ) -> DeleteProjectResourcePolicyActionResult:
        name = action.name

        async with self._db.begin_session() as db_sess:
            delete_query = (
                sa.delete(ProjectResourcePolicyRow)
                .where(ProjectResourcePolicyRow.name == name)
                .returning(ProjectResourcePolicyRow.__table__.c)
            )
            result = await db_sess.execute(delete_query)

        return DeleteProjectResourcePolicyActionResult(project_resource_policy=result)
