import dataclasses
import logging

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import ObjectNotFound
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
        dict_props = dataclasses.asdict(props)
        dict_props["name"] = name
        # Ignore deprecated fields
        del dict_props["max_vfolder_size"]

        async with self._db.begin_session() as db_sess:
            new_row = ProjectResourcePolicyRow(**dict_props)
            db_sess.add(new_row)
            result = new_row.to_dataclass()
            await db_sess.flush()

        return CreateProjectResourcePolicyActionResult(project_resource_policy=result)

    async def modify_project_resource_policy(
        self, action: ModifyProjectResourcePolicyAction
    ) -> ModifyProjectResourcePolicyActionResult:
        name = action.name
        props = action.props

        async with self._db.begin_session() as db_sess:
            query = sa.select(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == name)
            db_row = (await db_sess.execute(query)).scalar_one_or_none()
            if db_row is None:
                raise ObjectNotFound(f"Project resource policy with name {name} not found.")

            props.set_attr(db_row)

        return ModifyProjectResourcePolicyActionResult(
            project_resource_policy=db_row.to_dataclass()
        )

    async def delete_project_resource_policy(
        self, action: DeleteProjectResourcePolicyAction
    ) -> DeleteProjectResourcePolicyActionResult:
        name = action.name

        async with self._db.begin_session() as db_sess:
            query = sa.select(ProjectResourcePolicyRow).where(ProjectResourcePolicyRow.name == name)
            db_row = (await db_sess.execute(query)).scalar_one_or_none()
            if not db_row:
                raise ObjectNotFound(f"Project resource policy with name {name} not found.")
            await db_sess.delete(db_row)

        return DeleteProjectResourcePolicyActionResult(
            project_resource_policy=db_row.to_dataclass()
        )
