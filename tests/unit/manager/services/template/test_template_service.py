"""
Tests for TemplateService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

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
            "requesting_group": "default",
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

    async def test_returns_full_data(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        user_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        template_data = _make_valid_task_template()
        mock_repo.get_task_template = AsyncMock(
            return_value={
                "template": template_data,
                "name": "test-template",
                "user_uuid": user_uuid,
                "group_id": group_id,
            }
        )

        action = GetTaskTemplateAction(template_id="tmpl-123")
        result = await service.get_task_template(action)

        assert result.template == template_data
        assert result.name == "test-template"
        assert result.user_uuid == user_uuid
        assert result.group_id == group_id

    async def test_json_string_template_parsed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        template_data = _make_valid_task_template()
        mock_repo.get_task_template = AsyncMock(
            return_value={
                "template": json.dumps(template_data),
                "name": "test",
                "user_uuid": uuid.uuid4(),
                "group_id": uuid.uuid4(),
            }
        )

        action = GetTaskTemplateAction(template_id="tmpl-123")
        result = await service.get_task_template(action)

        assert isinstance(result.template, dict)
        assert result.template["kind"] == "taskTemplate"

    async def test_nonexistent_id_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_task_template = AsyncMock(return_value=None)

        action = GetTaskTemplateAction(template_id="nonexistent")
        with pytest.raises(TaskTemplateNotFound):
            await service.get_task_template(action)


class TestListTaskTemplatesAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_returns_filtered_entries(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        user_uuid = uuid.uuid4()
        entries = [
            {"name": "t1", "id": "id1", "user_uuid": user_uuid},
            {"name": "t2", "id": "id2", "user_uuid": user_uuid},
        ]
        mock_repo.list_task_templates = AsyncMock(return_value=entries)

        action = ListTaskTemplatesAction(user_uuid=user_uuid)
        result = await service.list_task_templates(action)

        assert len(result.entries) == 2
        mock_repo.list_task_templates.assert_called_once_with(user_uuid)

    async def test_empty_returns_empty_entries(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.list_task_templates = AsyncMock(return_value=[])

        action = ListTaskTemplatesAction(user_uuid=uuid.uuid4())
        result = await service.list_task_templates(action)

        assert result.entries == []


class TestUpdateTaskTemplateAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=TemplateRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    @pytest.fixture
    def base_action_kwargs(self) -> dict[str, Any]:
        return {
            "template_id": "tmpl-existing",
            "domain_name": "default",
            "requesting_group": "default",
            "requester_uuid": uuid.uuid4(),
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
    ) -> None:
        mock_repo.task_template_exists = AsyncMock(return_value=True)
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))
        mock_repo.update_task_template = AsyncMock(return_value=1)

        action = UpdateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template("updated"))],
        )
        result = await service.update_task_template(action)

        assert result is not None
        mock_repo.update_task_template.assert_called_once()

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.task_template_exists = AsyncMock(return_value=False)

        action = UpdateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        with pytest.raises(TaskTemplateNotFound):
            await service.update_task_template(action)

    async def test_invalid_template_raises_error(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.task_template_exists = AsyncMock(return_value=True)
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))

        bad_template = _make_valid_task_template()
        bad_template["kind"] = "wrong_kind"

        action = UpdateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=bad_template)],
        )
        with pytest.raises(Exception):
            await service.update_task_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.task_template_exists = AsyncMock(return_value=True)
        mock_repo.resolve_owner = AsyncMock(return_value=(uuid.uuid4(), uuid.uuid4()))
        mock_repo.update_task_template = AsyncMock(return_value=0)

        action = UpdateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        with pytest.raises(DBOperationFailed):
            await service.update_task_template(action)


class TestDeleteTaskTemplateAction:
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
        mock_repo.task_template_exists = AsyncMock(return_value=True)
        mock_repo.soft_delete_template = AsyncMock(return_value=1)

        action = DeleteTaskTemplateAction(template_id="tmpl-to-delete")
        result = await service.delete_task_template(action)

        assert result is not None
        mock_repo.soft_delete_template.assert_called_once_with("tmpl-to-delete", TemplateType.TASK)

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.task_template_exists = AsyncMock(return_value=False)

        action = DeleteTaskTemplateAction(template_id="nonexistent")
        with pytest.raises(TaskTemplateNotFound):
            await service.delete_task_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.task_template_exists = AsyncMock(return_value=True)
        mock_repo.soft_delete_template = AsyncMock(return_value=0)

        action = DeleteTaskTemplateAction(template_id="tmpl-x")
        with pytest.raises(DBOperationFailed):
            await service.delete_task_template(action)


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
            "requesting_group": "default",
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
        mock_repo.get_cluster_template = AsyncMock(return_value=template_data)

        action = GetClusterTemplateAction(template_id="cluster-1")
        result = await service.get_cluster_template(action)

        assert result.template == template_data

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template = AsyncMock(return_value=None)

        action = GetClusterTemplateAction(template_id="nonexistent")
        with pytest.raises(TaskTemplateNotFound):
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
        mock_repo.list_accessible_cluster_templates = AsyncMock(return_value=entries)

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
        mock_repo.list_accessible_cluster_templates.assert_called_once_with(
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
        mock_repo.list_accessible_cluster_templates = AsyncMock(return_value=[])

        action = ListClusterTemplatesAction(
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            domain_name="default",
            is_superadmin=False,
            list_all=False,
            group_id_filter=group_id,
        )
        await service.list_cluster_templates(action)

        mock_repo.list_accessible_cluster_templates.assert_called_once_with(
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
        mock_repo.cluster_template_exists = AsyncMock(return_value=True)
        mock_repo.update_cluster_template = AsyncMock(return_value=1)

        action = UpdateClusterTemplateAction(
            template_id="cluster-1",
            template_data=_make_valid_cluster_template("updated-cluster"),
        )
        result = await service.update_cluster_template(action)

        assert result is not None
        mock_repo.update_cluster_template.assert_called_once()

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.cluster_template_exists = AsyncMock(return_value=False)

        action = UpdateClusterTemplateAction(
            template_id="nonexistent",
            template_data=_make_valid_cluster_template(),
        )
        with pytest.raises(TaskTemplateNotFound):
            await service.update_cluster_template(action)

    async def test_no_master_node_raises_invalid_argument(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.cluster_template_exists = AsyncMock(return_value=True)

        template = _make_valid_cluster_template()
        template["spec"]["nodes"] = [
            {"role": "worker", "session_template": uuid.uuid4().hex, "replicas": 2},
        ]

        action = UpdateClusterTemplateAction(
            template_id="cluster-1",
            template_data=template,
        )
        with pytest.raises(InvalidArgument, match="main"):
            await service.update_cluster_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.cluster_template_exists = AsyncMock(return_value=True)
        mock_repo.update_cluster_template = AsyncMock(return_value=0)

        action = UpdateClusterTemplateAction(
            template_id="cluster-1",
            template_data=_make_valid_cluster_template(),
        )
        with pytest.raises(DBOperationFailed):
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
        mock_repo.cluster_template_exists = AsyncMock(return_value=True)
        mock_repo.soft_delete_template = AsyncMock(return_value=1)

        action = DeleteClusterTemplateAction(template_id="cluster-to-delete")
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
        mock_repo.cluster_template_exists = AsyncMock(return_value=False)

        action = DeleteClusterTemplateAction(template_id="nonexistent")
        with pytest.raises(TaskTemplateNotFound):
            await service.delete_cluster_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.cluster_template_exists = AsyncMock(return_value=True)
        mock_repo.soft_delete_template = AsyncMock(return_value=0)

        action = DeleteClusterTemplateAction(template_id="cluster-x")
        with pytest.raises(DBOperationFailed):
            await service.delete_cluster_template(action)
