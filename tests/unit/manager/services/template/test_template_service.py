"""
Tests for TemplateService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import json
import uuid
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.common.identifier.project import ProjectID
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import DBOperationFailed, TaskTemplateNotFound
from ai.backend.manager.exceptions import InvalidArgument
from ai.backend.manager.models.session_template import TemplateType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.template.repository import TemplateRepository
from ai.backend.manager.services.template.actions.create_cluster_template import (
    CreateClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.create_task_template import (
    CreateTaskTemplateAction,
    TaskTemplateItemInput,
)
from ai.backend.manager.services.template.actions.delete_cluster_template import (
    DeleteClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.delete_task_template import (
    DeleteTaskTemplateAction,
)
from ai.backend.manager.services.template.actions.get_cluster_template import (
    GetClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.get_task_template import (
    GetTaskTemplateAction,
)
from ai.backend.manager.services.template.actions.list_cluster_templates import (
    ListClusterTemplatesAction,
)
from ai.backend.manager.services.template.actions.list_task_templates import (
    ListTaskTemplatesAction,
)
from ai.backend.manager.services.template.actions.update_cluster_template import (
    UpdateClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.update_task_template import (
    UpdateTaskTemplateAction,
)
from ai.backend.manager.services.template.service import TemplateService

_CLUSTER_TEMPLATE_OWNER_UUID = uuid.UUID(int=1)
_OTHER_USER_UUID = uuid.UUID(int=2)
_CLUSTER_TEMPLATE_DOMAIN = "template-domain"
_OTHER_DOMAIN = "other-domain"
_CLUSTER_TEMPLATE_OWNER = {
    "user_uuid": _CLUSTER_TEMPLATE_OWNER_UUID,
    "domain_name": _CLUSTER_TEMPLATE_DOMAIN,
}


@dataclass(frozen=True)
class _ClusterTemplateRequesterCase:
    label: str
    requester_uuid: uuid.UUID
    requester_role: UserRole
    requester_domain: str


def _acting_as(
    user_id: uuid.UUID, role: UserRole, domain_name: str
) -> AbstractContextManager[None]:
    return with_user(
        UserData(
            user_id=user_id,
            is_authorized=True,
            is_admin=role in (UserRole.ADMIN, UserRole.SUPERADMIN),
            is_superadmin=role == UserRole.SUPERADMIN,
            role=role,
            domain_name=domain_name,
        )
    )


def _make_valid_task_template(name: str = "my-task") -> dict[str, Any]:
    return {
        "api_version": "v1",
        "kind": "taskTemplate",
        "metadata": {"name": name},
        "spec": {
            "kernel": {
                "image": "cr.backend.ai/stable/python:3.9-ubuntu20.04",
            },
        },
    }


def _make_valid_cluster_template(
    name: str = "my-cluster",
    session_template_uuid: str | None = None,
) -> dict[str, Any]:
    st_uuid = session_template_uuid or uuid.uuid4().hex
    return {
        "api_version": "v1",
        "kind": "clusterTemplate",
        "mode": "multi-node",
        "metadata": {"name": name},
        "spec": {
            "nodes": [
                {
                    "role": "main",
                    "session_template": st_uuid,
                    "replicas": 1,
                },
                {
                    "role": "worker",
                    "session_template": st_uuid,
                    "replicas": 3,
                },
            ],
        },
    }


class TestCreateTaskTemplateAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    @pytest.fixture
    def base_action_kwargs(self) -> dict[str, Any]:
        return {
            "domain_name": "default",
            "requesting_project": ProjectID(uuid.uuid4()),
            "requester_uuid": uuid.uuid4(),
            "requester_access_key": "AKIAIOSFODNN7EXAMPLE",
            "requester_role": UserRole.USER,
            "requester_domain": "default",
            "owner_access_key": None,
        }

    async def test_valid_template_returns_id_and_owner(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        owner_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        mock_repo.resolve_owner = AsyncMock(return_value=(owner_uuid, group_id))
        mock_repo.create_task_templates = AsyncMock(
            return_value=[{"id": "abc123", "user": owner_uuid.hex}]
        )

        action = CreateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        result = await service.create_task_template(action)

        assert len(result.created) == 1
        assert result.created[0].id == "abc123"
        assert result.created[0].user == owner_uuid.hex
        mock_repo.create_task_templates.assert_called_once()

    async def test_batch_creation_multiple_items(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        owner1 = uuid.uuid4()
        owner2 = uuid.uuid4()
        group1 = uuid.uuid4()
        group2 = uuid.uuid4()
        default_owner = uuid.uuid4()
        default_group = uuid.uuid4()
        mock_repo.resolve_owner = AsyncMock(return_value=(default_owner, default_group))
        mock_repo.create_task_templates = AsyncMock(
            return_value=[
                {"id": "id1", "user": owner1.hex},
                {"id": "id2", "user": owner2.hex},
            ]
        )

        action = CreateTaskTemplateAction(
            **base_action_kwargs,
            items=[
                TaskTemplateItemInput(
                    template=_make_valid_task_template("t1"),
                    user_uuid=owner1,
                    group_id=group1,
                ),
                TaskTemplateItemInput(
                    template=_make_valid_task_template("t2"),
                    user_uuid=owner2,
                    group_id=group2,
                ),
            ],
        )
        result = await service.create_task_template(action)

        assert len(result.created) == 2
        call_args = mock_repo.create_task_templates.call_args
        items_arg = call_args[0][1]
        assert items_arg[0]["user_uuid"] == owner1
        assert items_arg[0]["group_id"] == group1
        assert items_arg[1]["user_uuid"] == owner2
        assert items_arg[1]["group_id"] == group2

    async def test_invalid_kind_raises_error(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))

        bad_template = _make_valid_task_template()
        bad_template["kind"] = "invalid_kind"

        action = CreateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=bad_template)],
        )
        with pytest.raises(Exception):
            await service.create_task_template(action)

    async def test_reserved_vfolder_mount_raises_invalid_argument(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))

        template = _make_valid_task_template()
        template["spec"]["mounts"] = {"my-vfolder": "/home/work/.ssh"}

        action = CreateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=template)],
        )
        with pytest.raises(InvalidArgument, match="reserved"):
            await service.create_task_template(action)

    async def test_owner_access_key_override(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        override_owner = uuid.uuid4()
        override_group = uuid.uuid4()
        mock_repo.resolve_owner = AsyncMock(return_value=(override_owner, override_group))
        mock_repo.create_task_templates = AsyncMock(
            return_value=[{"id": "x", "user": override_owner.hex}]
        )

        base_action_kwargs["owner_access_key"] = "OVERRIDE_KEY"
        action = CreateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        result = await service.create_task_template(action)

        mock_repo.resolve_owner.assert_called_once()
        call_kwargs = mock_repo.resolve_owner.call_args
        assert call_kwargs[1]["owner_access_key"] == "OVERRIDE_KEY"
        assert result.created[0].user == override_owner.hex

    async def test_name_from_metadata_when_not_provided(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))
        mock_repo.create_task_templates = AsyncMock(return_value=[{"id": "x", "user": "u"}])

        action = CreateTaskTemplateAction(
            **base_action_kwargs,
            items=[
                TaskTemplateItemInput(template=_make_valid_task_template("from-meta"), name=None)
            ],
        )
        await service.create_task_template(action)

        items_arg = mock_repo.create_task_templates.call_args[0][1]
        assert items_arg[0]["name"] == "from-meta"


class TestGetTaskTemplateAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    @pytest.fixture
    def owner_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def stored_template(self, mock_repo: MagicMock, owner_uuid: uuid.UUID) -> dict[str, Any]:
        row = {
            "template": _make_valid_task_template(),
            "name": "test-template",
            "user_uuid": owner_uuid,
            "group_id": uuid.uuid4(),
            "domain_name": "default",
        }
        mock_repo.get_task_template = AsyncMock(return_value=row)
        return row

    async def test_returns_full_data_to_the_owner(
        self,
        service: TemplateService,
        owner_uuid: uuid.UUID,
        stored_template: dict[str, Any],
    ) -> None:
        action = GetTaskTemplateAction(
            template_id="tmpl-123",
        )
        with _acting_as(owner_uuid, UserRole.USER, "default"):
            result = await service.get_task_template(action)

        assert result.template == stored_template["template"]
        assert result.name == "test-template"
        assert result.user_uuid == owner_uuid
        assert result.group_id == stored_template["group_id"]

    async def test_json_string_template_parsed(
        self,
        service: TemplateService,
        owner_uuid: uuid.UUID,
        stored_template: dict[str, Any],
    ) -> None:
        stored_template["template"] = json.dumps(stored_template["template"])

        action = GetTaskTemplateAction(
            template_id="tmpl-123",
        )
        with _acting_as(owner_uuid, UserRole.USER, "default"):
            result = await service.get_task_template(action)

        assert isinstance(result.template, dict)
        assert result.template["kind"] == "taskTemplate"

    @pytest.mark.parametrize(
        ("role", "domain"),
        [(UserRole.SUPERADMIN, "other"), (UserRole.ADMIN, "default")],
        ids=["superadmin", "admin_of_the_template_domain"],
    )
    async def test_an_admin_in_scope_reads_another_users_template(
        self,
        service: TemplateService,
        stored_template: dict[str, Any],
        role: UserRole,
        domain: str,
    ) -> None:
        action = GetTaskTemplateAction(
            template_id="tmpl-123",
        )
        with _acting_as(uuid.uuid4(), role, domain):
            result = await service.get_task_template(action)

        assert result.name == "test-template"

    @pytest.mark.parametrize(
        ("role", "domain"),
        [(UserRole.USER, "default"), (UserRole.ADMIN, "other")],
        ids=["another_user", "admin_of_another_domain"],
    )
    async def test_rejects_a_requester_outside_the_owner_scope(
        self,
        service: TemplateService,
        stored_template: dict[str, Any],
        role: UserRole,
        domain: str,
    ) -> None:
        action = GetTaskTemplateAction(
            template_id="tmpl-123",
        )
        with pytest.raises(NotEnoughPermission), _acting_as(uuid.uuid4(), role, domain):
            await service.get_task_template(action)

    async def test_nonexistent_id_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_task_template = AsyncMock(return_value=None)

        action = GetTaskTemplateAction(
            template_id="nonexistent",
        )
        with (
            pytest.raises(TaskTemplateNotFound),
            _acting_as(uuid.uuid4(), UserRole.USER, "default"),
        ):
            await service.get_task_template(action)


class TestListTaskTemplatesAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_superadmin_with_list_all_returns_every_template(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        user_uuid = uuid.uuid4()
        entries = [{"name": "t1"}, {"name": "t2"}]
        mock_repo.list_task_templates_all = AsyncMock(return_value=entries)

        action = ListTaskTemplatesAction(
            user_uuid=user_uuid,
            user_role=UserRole.SUPERADMIN,
            domain_name="default",
            is_superadmin=True,
            list_all=True,
        )
        result = await service.list_task_templates(action)

        assert result.entries == entries
        mock_repo.list_task_templates_all.assert_called_once_with(user_uuid)

    @pytest.mark.parametrize(
        ("role", "is_superadmin", "list_all"),
        [
            (UserRole.USER, False, True),
            (UserRole.ADMIN, False, False),
            (UserRole.SUPERADMIN, True, False),
        ],
        ids=["user_asking_for_all", "domain_admin", "superadmin_without_all"],
    )
    async def test_others_get_only_the_accessible_templates(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        role: UserRole,
        is_superadmin: bool,
        list_all: bool,
    ) -> None:
        user_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        entries = [{"name": "mine"}]
        mock_repo.list_accessible_templates = AsyncMock(return_value=entries)
        mock_repo.list_task_templates_all = AsyncMock(return_value=[])

        action = ListTaskTemplatesAction(
            user_uuid=user_uuid,
            user_role=role,
            domain_name="default",
            is_superadmin=is_superadmin,
            list_all=list_all,
            group_id_filter=group_id,
        )
        result = await service.list_task_templates(action)

        assert result.entries == entries
        mock_repo.list_task_templates_all.assert_not_called()
        mock_repo.list_accessible_templates.assert_called_once_with(
            TemplateType.TASK,
            user_uuid,
            role,
            "default",
            allowed_types=["user", "group"],
            group_id_filter=group_id,
        )


class TestUpdateTaskTemplateAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    @pytest.fixture
    def owner_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def stored_template(self, mock_repo: MagicMock, owner_uuid: uuid.UUID) -> dict[str, Any]:
        row = {
            "template": _make_valid_task_template(),
            "name": "test-template",
            "user_uuid": owner_uuid,
            "group_id": uuid.uuid4(),
            "domain_name": "default",
        }
        mock_repo.get_task_template = AsyncMock(return_value=row)
        return row

    @pytest.fixture
    def base_action_kwargs(self, owner_uuid: uuid.UUID) -> dict[str, Any]:
        return {
            "template_id": "tmpl-existing",
            "domain_name": "default",
            "requesting_project": ProjectID(uuid.uuid4()),
            "requester_uuid": owner_uuid,
            "requester_access_key": "AKIAIOSFODNN7EXAMPLE",
            "requester_role": UserRole.USER,
            "requester_domain": "default",
            "owner_access_key": None,
        }

    async def test_successful_update(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
        stored_template: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))
        mock_repo.update_task_template = AsyncMock(return_value=1)

        action = UpdateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template("updated"))],
        )
        with _acting_as(action.requester_uuid, action.requester_role, action.requester_domain):
            result = await service.update_task_template(action)

        assert result is not None
        mock_repo.update_task_template.assert_called_once()

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.get_task_template = AsyncMock(return_value=None)

        action = UpdateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        with (
            pytest.raises(TaskTemplateNotFound),
            _acting_as(action.requester_uuid, action.requester_role, action.requester_domain),
        ):
            await service.update_task_template(action)

    async def test_invalid_template_raises_error(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
        stored_template: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))

        bad_template = _make_valid_task_template()
        bad_template["kind"] = "wrong_kind"

        action = UpdateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=bad_template)],
        )
        with (
            pytest.raises(Exception),
            _acting_as(action.requester_uuid, action.requester_role, action.requester_domain),
        ):
            await service.update_task_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
        stored_template: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))
        mock_repo.update_task_template = AsyncMock(return_value=0)

        action = UpdateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        with (
            pytest.raises(DBOperationFailed),
            _acting_as(action.requester_uuid, action.requester_role, action.requester_domain),
        ):
            await service.update_task_template(action)

    @pytest.mark.parametrize(
        ("role", "domain"),
        [(UserRole.USER, "default"), (UserRole.ADMIN, "other")],
        ids=["another_user", "admin_of_another_domain"],
    )
    async def test_rejects_a_requester_outside_the_owner_scope(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
        stored_template: dict[str, Any],
        role: UserRole,
        domain: str,
    ) -> None:
        mock_repo.update_task_template = AsyncMock(return_value=1)
        kwargs = {
            **base_action_kwargs,
            "requester_uuid": uuid.uuid4(),
            "requester_role": role,
            "requester_domain": domain,
        }

        action = UpdateTaskTemplateAction(
            **kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        with (
            pytest.raises(NotEnoughPermission),
            _acting_as(action.requester_uuid, action.requester_role, action.requester_domain),
        ):
            await service.update_task_template(action)
        mock_repo.update_task_template.assert_not_called()

    async def test_an_admin_of_the_template_domain_updates_it(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
        stored_template: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))
        mock_repo.update_task_template = AsyncMock(return_value=1)
        kwargs = {
            **base_action_kwargs,
            "requester_uuid": uuid.uuid4(),
            "requester_role": UserRole.ADMIN,
        }

        action = UpdateTaskTemplateAction(
            **kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        with _acting_as(action.requester_uuid, action.requester_role, action.requester_domain):
            await service.update_task_template(action)

        mock_repo.update_task_template.assert_called_once()


class TestDeleteTaskTemplateAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    @pytest.fixture
    def owner_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def stored_template(self, mock_repo: MagicMock, owner_uuid: uuid.UUID) -> dict[str, Any]:
        row = {
            "template": _make_valid_task_template(),
            "name": "test-template",
            "user_uuid": owner_uuid,
            "group_id": uuid.uuid4(),
            "domain_name": "default",
        }
        mock_repo.get_task_template = AsyncMock(return_value=row)
        return row

    async def test_soft_delete_success(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        owner_uuid: uuid.UUID,
        stored_template: dict[str, Any],
    ) -> None:
        mock_repo.soft_delete_template = AsyncMock(return_value=1)

        action = DeleteTaskTemplateAction(
            template_id="tmpl-to-delete",
        )
        with _acting_as(owner_uuid, UserRole.USER, "default"):
            result = await service.delete_task_template(action)

        assert result is not None
        mock_repo.soft_delete_template.assert_called_once_with("tmpl-to-delete", TemplateType.TASK)

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_task_template = AsyncMock(return_value=None)

        action = DeleteTaskTemplateAction(
            template_id="nonexistent",
        )
        with (
            pytest.raises(TaskTemplateNotFound),
            _acting_as(uuid.uuid4(), UserRole.USER, "default"),
        ):
            await service.delete_task_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        owner_uuid: uuid.UUID,
        stored_template: dict[str, Any],
    ) -> None:
        mock_repo.soft_delete_template = AsyncMock(return_value=0)

        action = DeleteTaskTemplateAction(
            template_id="tmpl-x",
        )
        with pytest.raises(DBOperationFailed), _acting_as(owner_uuid, UserRole.USER, "default"):
            await service.delete_task_template(action)

    @pytest.mark.parametrize(
        ("role", "domain"),
        [(UserRole.USER, "default"), (UserRole.ADMIN, "other")],
        ids=["another_user", "admin_of_another_domain"],
    )
    async def test_rejects_a_requester_outside_the_owner_scope(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        stored_template: dict[str, Any],
        role: UserRole,
        domain: str,
    ) -> None:
        mock_repo.soft_delete_template = AsyncMock(return_value=1)

        action = DeleteTaskTemplateAction(
            template_id="tmpl-x",
        )
        with pytest.raises(NotEnoughPermission), _acting_as(uuid.uuid4(), role, domain):
            await service.delete_task_template(action)
        mock_repo.soft_delete_template.assert_not_called()

    @pytest.mark.parametrize(
        ("role", "domain"),
        [(UserRole.SUPERADMIN, "other"), (UserRole.ADMIN, "default")],
        ids=["superadmin", "admin_of_the_template_domain"],
    )
    async def test_an_admin_in_scope_deletes_another_users_template(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        stored_template: dict[str, Any],
        role: UserRole,
        domain: str,
    ) -> None:
        mock_repo.soft_delete_template = AsyncMock(return_value=1)

        action = DeleteTaskTemplateAction(
            template_id="tmpl-x",
        )
        with _acting_as(uuid.uuid4(), role, domain):
            await service.delete_task_template(action)

        mock_repo.soft_delete_template.assert_called_once_with("tmpl-x", TemplateType.TASK)


class TestCreateClusterTemplateAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    @pytest.fixture
    def base_action_kwargs(self) -> dict[str, Any]:
        return {
            "domain_name": "default",
            "requesting_project": ProjectID(uuid.uuid4()),
            "requester_uuid": uuid.uuid4(),
            "requester_access_key": "AKIAIOSFODNN7EXAMPLE",
            "requester_role": UserRole.USER,
            "requester_domain": "default",
            "owner_access_key": None,
        }

    async def test_valid_cluster_returns_id_and_owner_hex(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        owner_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        mock_repo.resolve_owner = AsyncMock(return_value=(owner_uuid, group_id))
        mock_repo.create_cluster_template = AsyncMock(return_value="cluster-tmpl-id")

        action = CreateClusterTemplateAction(
            **base_action_kwargs,
            template_data=_make_valid_cluster_template(),
        )
        result = await service.create_cluster_template(action)

        assert result.id == "cluster-tmpl-id"
        assert result.user == owner_uuid.hex

    async def test_no_master_node_raises_invalid_argument(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))

        template = _make_valid_cluster_template()
        template["spec"]["nodes"] = [
            {"role": "worker", "session_template": uuid.uuid4().hex, "replicas": 2},
        ]

        action = CreateClusterTemplateAction(
            **base_action_kwargs,
            template_data=template,
        )
        with pytest.raises(InvalidArgument, match="main"):
            await service.create_cluster_template(action)

    async def test_master_replicas_not_one_raises_invalid_argument(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))

        template = _make_valid_cluster_template()
        template["spec"]["nodes"][0]["replicas"] = 2

        action = CreateClusterTemplateAction(
            **base_action_kwargs,
            template_data=template,
        )
        with pytest.raises(InvalidArgument, match="main"):
            await service.create_cluster_template(action)

    async def test_invalid_kind_raises_error(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))

        template = _make_valid_cluster_template()
        template["kind"] = "wrongKind"

        action = CreateClusterTemplateAction(
            **base_action_kwargs,
            template_data=template,
        )
        with pytest.raises(Exception):
            await service.create_cluster_template(action)


class TestGetClusterTemplateAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_returns_full_specification(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        template_data = {"spec": {"nodes": []}, "metadata": {"name": "test"}}
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=_CLUSTER_TEMPLATE_OWNER)
        mock_repo.get_cluster_template = AsyncMock(return_value=template_data)

        action = GetClusterTemplateAction(
            template_id="cluster-1",
        )
        with _acting_as(_CLUSTER_TEMPLATE_OWNER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN):
            result = await service.get_cluster_template(action)

        assert result.template == template_data

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=None)

        action = GetClusterTemplateAction(
            template_id="nonexistent",
        )
        with (
            pytest.raises(TaskTemplateNotFound),
            _acting_as(_CLUSTER_TEMPLATE_OWNER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN),
        ):
            await service.get_cluster_template(action)


class TestListClusterTemplatesAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_superadmin_list_all_returns_domain_wide(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        user_uuid = uuid.uuid4()
        entries = [{"name": "cluster-1"}, {"name": "cluster-2"}]
        mock_repo.list_cluster_templates_all = AsyncMock(return_value=entries)

        action = ListClusterTemplatesAction(
            user_uuid=user_uuid,
            user_role=UserRole.SUPERADMIN,
            domain_name="default",
            is_superadmin=True,
            list_all=True,
            group_id_filter=None,
        )
        result = await service.list_cluster_templates(action)

        assert len(result.entries) == 2
        mock_repo.list_cluster_templates_all.assert_called_once_with(user_uuid)

    async def test_regular_user_returns_accessible_only(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        user_uuid = uuid.uuid4()
        entries = [{"name": "my-cluster"}]
        mock_repo.list_accessible_templates = AsyncMock(return_value=entries)

        action = ListClusterTemplatesAction(
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            domain_name="default",
            is_superadmin=False,
            list_all=False,
            group_id_filter=None,
        )
        result = await service.list_cluster_templates(action)

        assert len(result.entries) == 1
        mock_repo.list_accessible_templates.assert_called_once_with(
            TemplateType.CLUSTER,
            user_uuid,
            UserRole.USER,
            "default",
            allowed_types=["user", "group"],
            group_id_filter=None,
        )

    async def test_group_id_filter_works(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        user_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        mock_repo.list_accessible_templates = AsyncMock(return_value=[])

        action = ListClusterTemplatesAction(
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            domain_name="default",
            is_superadmin=False,
            list_all=False,
            group_id_filter=group_id,
        )
        await service.list_cluster_templates(action)

        mock_repo.list_accessible_templates.assert_called_once_with(
            TemplateType.CLUSTER,
            user_uuid,
            UserRole.USER,
            "default",
            allowed_types=["user", "group"],
            group_id_filter=group_id,
        )


class TestUpdateClusterTemplateAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_valid_update(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=_CLUSTER_TEMPLATE_OWNER)
        mock_repo.update_cluster_template = AsyncMock(return_value=1)

        action = UpdateClusterTemplateAction(
            template_id="cluster-1",
            template_data=_make_valid_cluster_template("updated-cluster"),
        )
        with _acting_as(_CLUSTER_TEMPLATE_OWNER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN):
            result = await service.update_cluster_template(action)

        assert result is not None
        mock_repo.update_cluster_template.assert_called_once()

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=None)

        action = UpdateClusterTemplateAction(
            template_id="nonexistent",
            template_data=_make_valid_cluster_template(),
        )
        with (
            pytest.raises(TaskTemplateNotFound),
            _acting_as(_CLUSTER_TEMPLATE_OWNER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN),
        ):
            await service.update_cluster_template(action)

    async def test_no_master_node_raises_invalid_argument(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=_CLUSTER_TEMPLATE_OWNER)

        template = _make_valid_cluster_template()
        template["spec"]["nodes"] = [
            {"role": "worker", "session_template": uuid.uuid4().hex, "replicas": 2},
        ]

        action = UpdateClusterTemplateAction(
            template_id="cluster-1",
            template_data=template,
        )
        with (
            pytest.raises(InvalidArgument, match="main"),
            _acting_as(_CLUSTER_TEMPLATE_OWNER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN),
        ):
            await service.update_cluster_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=_CLUSTER_TEMPLATE_OWNER)
        mock_repo.update_cluster_template = AsyncMock(return_value=0)

        action = UpdateClusterTemplateAction(
            template_id="cluster-1",
            template_data=_make_valid_cluster_template(),
        )
        with (
            pytest.raises(DBOperationFailed),
            _acting_as(_CLUSTER_TEMPLATE_OWNER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN),
        ):
            await service.update_cluster_template(action)


class TestDeleteClusterTemplateAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_soft_delete_success(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=_CLUSTER_TEMPLATE_OWNER)
        mock_repo.soft_delete_template = AsyncMock(return_value=1)

        action = DeleteClusterTemplateAction(
            template_id="cluster-to-delete",
        )
        with _acting_as(_CLUSTER_TEMPLATE_OWNER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN):
            result = await service.delete_cluster_template(action)

        assert result is not None
        mock_repo.soft_delete_template.assert_called_once_with(
            "cluster-to-delete", TemplateType.CLUSTER
        )

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=None)

        action = DeleteClusterTemplateAction(
            template_id="nonexistent",
        )
        with (
            pytest.raises(TaskTemplateNotFound),
            _acting_as(_CLUSTER_TEMPLATE_OWNER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN),
        ):
            await service.delete_cluster_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=_CLUSTER_TEMPLATE_OWNER)
        mock_repo.soft_delete_template = AsyncMock(return_value=0)

        action = DeleteClusterTemplateAction(
            template_id="cluster-x",
        )
        with (
            pytest.raises(DBOperationFailed),
            _acting_as(_CLUSTER_TEMPLATE_OWNER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN),
        ):
            await service.delete_cluster_template(action)


class TestClusterTemplateAccess:
    @pytest.fixture
    def mock_repo_holding_a_cluster_template(self) -> MagicMock:
        mock_repo = MagicMock(spec=TemplateRepository)
        mock_repo.get_cluster_template_owner = AsyncMock(return_value=_CLUSTER_TEMPLATE_OWNER)
        mock_repo.get_cluster_template = AsyncMock(return_value={"metadata": {"name": "test"}})
        mock_repo.update_cluster_template = AsyncMock(return_value=1)
        mock_repo.soft_delete_template = AsyncMock(return_value=1)
        return mock_repo

    @pytest.fixture
    def service(self, mock_repo_holding_a_cluster_template: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo_holding_a_cluster_template)

    @pytest.mark.parametrize(
        "case",
        [
            _ClusterTemplateRequesterCase(
                label="owner",
                requester_uuid=_CLUSTER_TEMPLATE_OWNER_UUID,
                requester_role=UserRole.USER,
                requester_domain=_CLUSTER_TEMPLATE_DOMAIN,
            ),
            _ClusterTemplateRequesterCase(
                label="admin-of-the-template-domain",
                requester_uuid=_OTHER_USER_UUID,
                requester_role=UserRole.ADMIN,
                requester_domain=_CLUSTER_TEMPLATE_DOMAIN,
            ),
            _ClusterTemplateRequesterCase(
                label="superadmin-of-another-domain",
                requester_uuid=_OTHER_USER_UUID,
                requester_role=UserRole.SUPERADMIN,
                requester_domain=_OTHER_DOMAIN,
            ),
        ],
        ids=lambda case: case.label,
    )
    async def test_get_passes_for_allowed_requester(
        self,
        service: TemplateService,
        case: _ClusterTemplateRequesterCase,
    ) -> None:
        action = GetClusterTemplateAction(
            template_id="cluster-1",
        )

        with _acting_as(case.requester_uuid, case.requester_role, case.requester_domain):
            result = await service.get_cluster_template(action)

        assert result.template == {"metadata": {"name": "test"}}

    @pytest.mark.parametrize(
        "case",
        [
            _ClusterTemplateRequesterCase(
                label="another-user-of-the-domain",
                requester_uuid=_OTHER_USER_UUID,
                requester_role=UserRole.USER,
                requester_domain=_CLUSTER_TEMPLATE_DOMAIN,
            ),
            _ClusterTemplateRequesterCase(
                label="monitor-of-the-domain",
                requester_uuid=_OTHER_USER_UUID,
                requester_role=UserRole.MONITOR,
                requester_domain=_CLUSTER_TEMPLATE_DOMAIN,
            ),
            _ClusterTemplateRequesterCase(
                label="admin-of-another-domain",
                requester_uuid=_OTHER_USER_UUID,
                requester_role=UserRole.ADMIN,
                requester_domain=_OTHER_DOMAIN,
            ),
        ],
        ids=lambda case: case.label,
    )
    async def test_get_rejects_other_requester(
        self,
        service: TemplateService,
        case: _ClusterTemplateRequesterCase,
    ) -> None:
        action = GetClusterTemplateAction(
            template_id="cluster-1",
        )

        with (
            pytest.raises(NotEnoughPermission),
            _acting_as(case.requester_uuid, case.requester_role, case.requester_domain),
        ):
            await service.get_cluster_template(action)

    async def test_update_rejects_another_user_without_writing(
        self,
        service: TemplateService,
        mock_repo_holding_a_cluster_template: MagicMock,
    ) -> None:
        action = UpdateClusterTemplateAction(
            template_id="cluster-1",
            template_data=_make_valid_cluster_template(),
        )

        with (
            pytest.raises(NotEnoughPermission),
            _acting_as(_OTHER_USER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN),
        ):
            await service.update_cluster_template(action)

        mock_repo_holding_a_cluster_template.update_cluster_template.assert_not_called()

    async def test_delete_rejects_another_user_without_writing(
        self,
        service: TemplateService,
        mock_repo_holding_a_cluster_template: MagicMock,
    ) -> None:
        action = DeleteClusterTemplateAction(
            template_id="cluster-1",
        )

        with (
            pytest.raises(NotEnoughPermission),
            _acting_as(_OTHER_USER_UUID, UserRole.USER, _CLUSTER_TEMPLATE_DOMAIN),
        ):
            await service.delete_cluster_template(action)

        mock_repo_holding_a_cluster_template.soft_delete_template.assert_not_called()
