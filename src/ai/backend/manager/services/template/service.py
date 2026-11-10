from __future__ import annotations

import logging
import uuid
from typing import Any, Final

from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.user import UserID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.session_template.types import (
    ClusterTemplate,
    TaskTemplate,
    TemplateType,
)
from ai.backend.manager.errors.resource import DBOperationFailed, SessionTemplateNotFound
from ai.backend.manager.models.session_template.scopes import (
    ProjectSessionTemplateTarget,
    SessionTemplateTarget,
    UserSessionTemplateTarget,
)
from ai.backend.manager.repositories.template.repository import TemplateRepository

from .actions.create_cluster_template import (
    CreateClusterTemplateAction,
    CreateClusterTemplateActionResult,
)
from .actions.create_task_template import (
    CreatedTaskTemplateItem,
    CreateTaskTemplateAction,
    CreateTaskTemplateActionResult,
)
from .actions.delete_cluster_template import (
    DeleteClusterTemplateAction,
    DeleteClusterTemplateActionResult,
)
from .actions.delete_task_template import (
    DeleteTaskTemplateAction,
    DeleteTaskTemplateActionResult,
)
from .actions.get_cluster_template import (
    GetClusterTemplateAction,
    GetClusterTemplateActionResult,
)
from .actions.get_task_template import (
    GetTaskTemplateAction,
    GetTaskTemplateActionResult,
)
from .actions.global_list_cluster_templates import (
    GlobalListClusterTemplatesAction,
    GlobalListClusterTemplatesActionResult,
)
from .actions.global_list_task_templates import (
    GlobalListTaskTemplatesAction,
    GlobalListTaskTemplatesActionResult,
)
from .actions.list_cluster_templates import (
    ListClusterTemplatesAction,
    ListClusterTemplatesActionResult,
)
from .actions.list_task_templates import (
    ListTaskTemplatesAction,
    ListTaskTemplatesActionResult,
)
from .actions.update_cluster_template import (
    UpdateClusterTemplateAction,
    UpdateClusterTemplateActionResult,
)
from .actions.update_task_template import (
    UpdateTaskTemplateAction,
    UpdateTaskTemplateActionResult,
)

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class TemplateService:
    _repository: TemplateRepository

    def __init__(self, *, repository: TemplateRepository) -> None:
        self._repository = repository

    # --- Task template operations ---

    async def create_task_template(
        self, action: CreateTaskTemplateAction
    ) -> CreateTaskTemplateActionResult:
        """Validate and create one or more task templates."""
        # Authorize owner against the pre-resolved project
        default_user_uuid, default_group_id = await self._repository.resolve_owner(
            requester_uuid=action.requester_uuid,
            requester_access_key=action.requester_access_key,
            requester_role=action.requester_role,
            requester_domain=action.requester_domain,
            requesting_domain=action.domain_name,
            requesting_project_id=action.requesting_project,
            owner_access_key=action.owner_access_key,
        )

        items: list[dict[str, Any]] = []
        for item_input in action.items:
            template_data = TaskTemplate.check(item_input.template)
            template_id = SessionTemplateID(uuid.uuid4())
            name = (
                item_input.name
                if item_input.name is not None
                else template_data["metadata"]["name"]
            )
            group_id = item_input.group_id if item_input.group_id is not None else default_group_id
            user_uuid = (
                item_input.user_uuid if item_input.user_uuid is not None else default_user_uuid
            )
            items.append({
                "id": template_id,
                "user_uuid": user_uuid,
                "group_id": group_id,
                "name": name,
                "template": template_data,
            })

        await self._repository.create_task_templates(action.domain_name, items)
        return CreateTaskTemplateActionResult(
            created=[
                CreatedTaskTemplateItem(id=item["id"], user=item["user_uuid"]) for item in items
            ]
        )

    async def list_task_templates(
        self, action: ListTaskTemplatesAction
    ) -> ListTaskTemplatesActionResult:
        entries = await self._repository.list_templates_in_scopes(
            TemplateType.TASK,
            await self._user_and_joined_project_scopes(action.user_uuid),
            action.group_id_filter,
        )
        return ListTaskTemplatesActionResult(entries=entries)

    async def global_list_task_templates(
        self, action: GlobalListTaskTemplatesAction
    ) -> GlobalListTaskTemplatesActionResult:
        entries = await self._repository.list_templates_in_global(TemplateType.TASK)
        return GlobalListTaskTemplatesActionResult(entries=entries)

    async def get_task_template(self, action: GetTaskTemplateAction) -> GetTaskTemplateActionResult:
        """Get a single task template by ID."""
        template = await self._repository.get_task_template(action.template_id)
        if template is None:
            raise SessionTemplateNotFound
        return GetTaskTemplateActionResult(template=template)

    async def update_task_template(
        self, action: UpdateTaskTemplateAction
    ) -> UpdateTaskTemplateActionResult:
        """Validate and update an existing task template."""
        exists = await self._repository.task_template_exists(action.template_id)
        if not exists:
            raise SessionTemplateNotFound

        # Authorize owner against the pre-resolved project
        default_user_uuid, default_group_id = await self._repository.resolve_owner(
            requester_uuid=action.requester_uuid,
            requester_access_key=action.requester_access_key,
            requester_role=action.requester_role,
            requester_domain=action.requester_domain,
            requesting_domain=action.domain_name,
            requesting_project_id=action.requesting_project,
            owner_access_key=action.owner_access_key,
        )

        for item_input in action.items:
            template_data = TaskTemplate.check(item_input.template)
            name = (
                item_input.name
                if item_input.name is not None
                else template_data["metadata"]["name"]
            )
            group_id = item_input.group_id if item_input.group_id is not None else default_group_id
            user_uuid = (
                item_input.user_uuid if item_input.user_uuid is not None else default_user_uuid
            )
            rowcount = await self._repository.update_task_template(
                action.template_id, group_id, user_uuid, name, template_data
            )
            if rowcount != 1:
                raise DBOperationFailed(f"Failed to update session template: {action.template_id}")
        return UpdateTaskTemplateActionResult()

    async def delete_task_template(
        self, action: DeleteTaskTemplateAction
    ) -> DeleteTaskTemplateActionResult:
        """Soft-delete a task template."""
        exists = await self._repository.task_template_exists(action.template_id)
        if not exists:
            raise SessionTemplateNotFound
        rowcount = await self._repository.soft_delete_template(
            action.template_id, TemplateType.TASK
        )
        if rowcount != 1:
            raise DBOperationFailed(f"Failed to delete session template: {action.template_id}")
        return DeleteTaskTemplateActionResult()

    # --- Cluster template operations ---

    async def create_cluster_template(
        self, action: CreateClusterTemplateAction
    ) -> CreateClusterTemplateActionResult:
        """Validate and create a cluster template."""
        # Authorize owner against the pre-resolved project
        owner_uuid, group_id = await self._repository.resolve_owner(
            requester_uuid=action.requester_uuid,
            requester_access_key=action.requester_access_key,
            requester_role=action.requester_role,
            requester_domain=action.requester_domain,
            requesting_domain=action.domain_name,
            requesting_project_id=action.requesting_project,
            owner_access_key=action.owner_access_key,
        )

        template_data = ClusterTemplate.check(action.template_data)
        name = template_data["metadata"]["name"]
        template_id = await self._repository.create_cluster_template(
            action.domain_name,
            group_id,
            owner_uuid,
            name,
            template_data,
        )
        return CreateClusterTemplateActionResult(id=template_id, user=owner_uuid)

    async def list_cluster_templates(
        self, action: ListClusterTemplatesAction
    ) -> ListClusterTemplatesActionResult:
        entries = await self._repository.list_templates_in_scopes(
            TemplateType.CLUSTER,
            await self._user_and_joined_project_scopes(action.user_uuid),
            action.group_id_filter,
        )
        return ListClusterTemplatesActionResult(entries=entries)

    async def global_list_cluster_templates(
        self, action: GlobalListClusterTemplatesAction
    ) -> GlobalListClusterTemplatesActionResult:
        entries = await self._repository.list_templates_in_global(TemplateType.CLUSTER)
        return GlobalListClusterTemplatesActionResult(entries=entries)

    async def get_cluster_template(
        self, action: GetClusterTemplateAction
    ) -> GetClusterTemplateActionResult:
        """Get a single cluster template by ID."""
        template = await self._repository.get_cluster_template(action.template_id)
        if template is None:
            raise SessionTemplateNotFound
        return GetClusterTemplateActionResult(template=template)

    async def update_cluster_template(
        self, action: UpdateClusterTemplateAction
    ) -> UpdateClusterTemplateActionResult:
        """Validate and update an existing cluster template."""
        exists = await self._repository.cluster_template_exists(action.template_id)
        if not exists:
            raise SessionTemplateNotFound
        template_data = ClusterTemplate.check(action.template_data)
        name = template_data["metadata"]["name"]
        rowcount = await self._repository.update_cluster_template(
            action.template_id, template_data, name
        )
        if rowcount != 1:
            raise DBOperationFailed(f"Failed to update cluster template: {action.template_id}")
        return UpdateClusterTemplateActionResult()

    async def delete_cluster_template(
        self, action: DeleteClusterTemplateAction
    ) -> DeleteClusterTemplateActionResult:
        """Soft-delete a cluster template."""
        exists = await self._repository.cluster_template_exists(action.template_id)
        if not exists:
            raise SessionTemplateNotFound
        rowcount = await self._repository.soft_delete_template(
            action.template_id, TemplateType.CLUSTER
        )
        if rowcount != 1:
            raise DBOperationFailed(f"Failed to delete cluster template: {action.template_id}")
        return DeleteClusterTemplateActionResult()

    async def _user_and_joined_project_scopes(self, user_id: UserID) -> list[SessionTemplateTarget]:
        joined_project_ids = await self._repository.joined_project_ids(user_id)
        return [
            UserSessionTemplateTarget(user_id=user_id),
            *(
                ProjectSessionTemplateTarget(project_id=project_id)
                for project_id in joined_project_ids
            ),
        ]
