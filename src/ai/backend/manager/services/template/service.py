from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from typing import Any, Final, cast

import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.json import load_json
from ai.backend.common.types import SessionTypes
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.session_template.types import TemplateType
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.resource import DBOperationFailed, SessionTemplateNotFound
from ai.backend.manager.exceptions import InvalidArgument
from ai.backend.manager.models.vfolder import verify_vfolder_name
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

_task_template_v1 = t.Dict({
    tx.AliasedKey(["api_version", "apiVersion"]): t.String,
    t.Key("kind"): t.Enum("taskTemplate", "task_template"),
    t.Key("metadata"): t.Dict({
        t.Key("name"): t.String,
        t.Key("tag", default=None): t.Null | t.String,
    }),
    t.Key("spec"): t.Dict({
        tx.AliasedKey(["type", "session_type", "sessionType"], default="interactive")
        >> "session_type": tx.Enum(SessionTypes),
        t.Key("kernel"): t.Dict({
            t.Key("image"): t.String,
            t.Key("architecture", default="x86_64"): t.Null | t.String,
            t.Key("environ", default={}): t.Null | t.Mapping(t.String, t.String),
            t.Key("run", default=None): t.Null
            | t.Dict({
                t.Key("bootstrap", default=None): t.Null | t.String,
                tx.AliasedKey(["startup", "startup_command", "startupCommand"], default=None)
                >> "startup_command": t.Null | t.String,
            }),
            t.Key("git", default=None): t.Null
            | t.Dict({
                t.Key("repository"): t.String,
                t.Key("commit", default=None): t.Null | t.String,
                t.Key("branch", default=None): t.Null | t.String,
                t.Key("credential", default=None): t.Null
                | t.Dict({
                    t.Key("username"): t.String,
                    t.Key("password"): t.String,
                }),
                tx.AliasedKey(["destination_dir", "destinationDir"], default=None)
                >> "dest_dir": t.Null | t.String,
            }),
        }),
        t.Key("scaling_group", default=None): t.Null | t.String,
        t.Key("mounts", default={}): t.Null | t.Mapping(t.String, t.Any),
        t.Key("resources", default=None): t.Null | t.Mapping(t.String, t.Any),
        tx.AliasedKey(["agent_list", "agentList"], default=None) >> "agent_list": t.Null
        | t.List(t.String),
    }),
}).allow_extra("*")


def _check_task_template(raw_data: Mapping[str, Any]) -> Mapping[str, Any]:
    data = _task_template_v1.check(raw_data)
    if mounts := data["spec"].get("mounts"):
        for p in mounts.values():
            if p is None:
                continue
            p = p.removeprefix("/home/work/")
            if not verify_vfolder_name(p):
                raise InvalidArgument(f"Path {p} is reserved for internal operations.")
    return cast(Mapping[str, Any], data)


_cluster_template_v1 = t.Dict({
    tx.AliasedKey(["api_version", "apiVersion"]): t.String,
    t.Key("kind"): t.Enum("clusterTemplate", "cluster_template"),
    t.Key("mode"): t.Enum("single-node", "multi-node"),
    t.Key("metadata"): t.Dict({
        t.Key("name"): t.String,
    }),
    t.Key("spec"): t.Dict({
        t.Key("environ", default={}): t.Null | t.Mapping(t.String, t.String),
        t.Key("mounts", default={}): t.Null | t.Mapping(t.String, t.Any),
        t.Key("nodes"): t.List(
            t.Dict({
                t.Key("role"): t.String,
                tx.AliasedKey(["session_template", "sessionTemplate"]): tx.UUID,
                t.Key("replicas", default=1): t.Int,
            })
        ),
    }),
}).allow_extra("*")


def _check_cluster_template(raw_data: Mapping[str, Any]) -> Mapping[str, Any]:
    data = _cluster_template_v1.check(raw_data)
    defined_roles: list[str] = []
    for node in data["spec"]["nodes"]:
        node["session_template"] = str(node["session_template"])
        if node["role"] in defined_roles:
            raise InvalidArgument("Each role can only be defined once")
        if node["role"] == DEFAULT_ROLE and node["replicas"] != 1:
            raise InvalidArgument(
                f"One and only one {DEFAULT_ROLE} node must be created per cluster",
            )
        defined_roles.append(node["role"])
    if DEFAULT_ROLE not in defined_roles:
        raise InvalidArgument(
            f"One and only one {DEFAULT_ROLE} node must be created per cluster",
        )
    return cast(Mapping[str, Any], data)


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
            template_data = _check_task_template(item_input.template)
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
        row = await self._repository.get_task_template(str(action.template_id))
        if row is None:
            raise SessionTemplateNotFound
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
        exists = await self._repository.task_template_exists(str(action.template_id))
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
            template_data = _check_task_template(item_input.template)
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
                str(action.template_id), group_id, user_uuid, name, template_data
            )
            if rowcount != 1:
                raise DBOperationFailed(f"Failed to update session template: {action.template_id}")
        return UpdateTaskTemplateActionResult()

    async def delete_task_template(
        self, action: DeleteTaskTemplateAction
    ) -> DeleteTaskTemplateActionResult:
        """Soft-delete a task template."""
        exists = await self._repository.task_template_exists(str(action.template_id))
        if not exists:
            raise SessionTemplateNotFound
        rowcount = await self._repository.soft_delete_template(
            str(action.template_id), TemplateType.TASK
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

        template_data = _check_cluster_template(action.template_data)
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
        template = await self._repository.get_cluster_template(str(action.template_id))
        if template is None:
            raise SessionTemplateNotFound
        return GetClusterTemplateActionResult(template=template)

    async def update_cluster_template(
        self, action: UpdateClusterTemplateAction
    ) -> UpdateClusterTemplateActionResult:
        """Validate and update an existing cluster template."""
        exists = await self._repository.cluster_template_exists(str(action.template_id))
        if not exists:
            raise SessionTemplateNotFound
        template_data = _check_cluster_template(action.template_data)
        name = template_data["metadata"]["name"]
        rowcount = await self._repository.update_cluster_template(
            str(action.template_id), template_data, name
        )
        if rowcount != 1:
            raise DBOperationFailed(f"Failed to update cluster template: {action.template_id}")
        return UpdateClusterTemplateActionResult()

    async def delete_cluster_template(
        self, action: DeleteClusterTemplateAction
    ) -> DeleteClusterTemplateActionResult:
        """Soft-delete a cluster template."""
        exists = await self._repository.cluster_template_exists(str(action.template_id))
        if not exists:
            raise SessionTemplateNotFound
        rowcount = await self._repository.soft_delete_template(
            str(action.template_id), TemplateType.CLUSTER
        )
        if rowcount != 1:
            raise DBOperationFailed(f"Failed to delete cluster template: {action.template_id}")
        return DeleteClusterTemplateActionResult()
