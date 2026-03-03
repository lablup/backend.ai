from __future__ import annotations

import logging
import uuid
from typing import Any, Final

from ai.backend.common.json import load_json
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.resource import DBOperationFailed, TaskTemplateNotFound
from ai.backend.manager.models.session_template import (
    TemplateType,
    check_cluster_template,
    check_task_template,
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

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class TemplateService:
    _repository: TemplateRepository

    def __init__(self, *, repository: TemplateRepository) -> None:
        self._repository = repository

    # --- Task template operations ---

    async def create_task_template(
        self, action: CreateTaskTemplateAction
    ) -> CreateTaskTemplateActionResult:
        """Validate and create one or more task templates."""
        # Resolve owner UUID and group ID (moved from handler)
        default_user_uuid, default_group_id = await self._repository.resolve_owner(
            requester_uuid=action.requester_uuid,
            requester_access_key=action.requester_access_key,
            requester_role=action.requester_role,
            requester_domain=action.requester_domain,
            requesting_domain=action.domain_name,
            requesting_group=action.requesting_group,
            owner_access_key=action.owner_access_key,
        )

        items: list[dict[str, Any]] = []
        for item_input in action.items:
            template_data = check_task_template(item_input.template)
            template_id = uuid.uuid4().hex
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

        results = await self._repository.create_task_templates(action.domain_name, items)
        return CreateTaskTemplateActionResult(
            created=[CreatedTaskTemplateItem(id=r["id"], user=r["user"]) for r in results]
        )

    async def list_task_templates(
        self, action: ListTaskTemplatesAction
    ) -> ListTaskTemplatesActionResult:
        """List all active task templates."""
        entries = await self._repository.list_task_templates(action.user_uuid)
        return ListTaskTemplatesActionResult(entries=entries)

    async def get_task_template(self, action: GetTaskTemplateAction) -> GetTaskTemplateActionResult:
        """Get a single task template by ID."""
        row = await self._repository.get_task_template(action.template_id)
        if row is None:
            raise TaskTemplateNotFound
        raw_template = row["template"]
        template: dict[str, Any] = (
            raw_template if isinstance(raw_template, dict) else dict(load_json(raw_template))
        )
        return GetTaskTemplateActionResult(
            template=template,
            name=row["name"],
            user_uuid=row["user_uuid"],
            group_id=row["group_id"],
        )

    async def update_task_template(
        self, action: UpdateTaskTemplateAction
    ) -> UpdateTaskTemplateActionResult:
        """Validate and update an existing task template."""
        exists = await self._repository.task_template_exists(action.template_id)
        if not exists:
            raise TaskTemplateNotFound

        # Resolve owner UUID and group ID (moved from handler)
        default_user_uuid, default_group_id = await self._repository.resolve_owner(
            requester_uuid=action.requester_uuid,
            requester_access_key=action.requester_access_key,
            requester_role=action.requester_role,
            requester_domain=action.requester_domain,
            requesting_domain=action.domain_name,
            requesting_group=action.requesting_group,
            owner_access_key=action.owner_access_key,
        )

        for item_input in action.items:
            template_data = check_task_template(item_input.template)
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
            raise TaskTemplateNotFound
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
        # Resolve owner UUID and group ID (moved from handler)
        owner_uuid, group_id = await self._repository.resolve_owner(
            requester_uuid=action.requester_uuid,
            requester_access_key=action.requester_access_key,
            requester_role=action.requester_role,
            requester_domain=action.requester_domain,
            requesting_domain=action.domain_name,
            requesting_group=action.requesting_group,
            owner_access_key=action.owner_access_key,
        )

        template_data = check_cluster_template(action.template_data)
        name = template_data["metadata"]["name"]
        template_id = await self._repository.create_cluster_template(
            action.domain_name,
            group_id,
            owner_uuid,
            name,
            template_data,
        )
        return CreateClusterTemplateActionResult(id=template_id, user=owner_uuid.hex)

    async def list_cluster_templates(
        self, action: ListClusterTemplatesAction
    ) -> ListClusterTemplatesActionResult:
        """List cluster templates with visibility control."""
        if action.is_superadmin and action.list_all:
            entries = await self._repository.list_cluster_templates_all(action.user_uuid)
        else:
            entries = await self._repository.list_accessible_cluster_templates(
                action.user_uuid,
                action.user_role,
                action.domain_name,
                allowed_types=["user", "group"],
                group_id_filter=action.group_id_filter,
            )
        return ListClusterTemplatesActionResult(entries=entries)

    async def get_cluster_template(
        self, action: GetClusterTemplateAction
    ) -> GetClusterTemplateActionResult:
        """Get a single cluster template by ID."""
        template = await self._repository.get_cluster_template(action.template_id)
        if template is None:
            raise TaskTemplateNotFound
        return GetClusterTemplateActionResult(template=template)

    async def update_cluster_template(
        self, action: UpdateClusterTemplateAction
    ) -> UpdateClusterTemplateActionResult:
        """Validate and update an existing cluster template."""
        exists = await self._repository.cluster_template_exists(action.template_id)
        if not exists:
            raise TaskTemplateNotFound
        template_data = check_cluster_template(action.template_data)
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
            raise TaskTemplateNotFound
        rowcount = await self._repository.soft_delete_template(
            action.template_id, TemplateType.CLUSTER
        )
        if rowcount != 1:
            raise DBOperationFailed(f"Failed to delete cluster template: {action.template_id}")
        return DeleteClusterTemplateActionResult()
