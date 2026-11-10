"""
Tests for TemplateService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.session_template.types import (
    SessionTemplateData,
    SessionTemplateWithOwnerEmailAndProjectName,
    TemplateType,
)
from ai.backend.manager.errors.resource import DBOperationFailed, SessionTemplateNotFound
from ai.backend.manager.exceptions import InvalidArgument
from ai.backend.manager.models.session_template.scopes import (
    ProjectSessionTemplateTarget,
    UserSessionTemplateTarget,
)
from ai.backend.manager.models.user.row import UserRole
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
from ai.backend.manager.services.template.actions.global_list_cluster_templates import (
    GlobalListClusterTemplatesAction,
)
from ai.backend.manager.services.template.actions.global_list_task_templates import (
    GlobalListTaskTemplatesAction,
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

_REQUESTER_ID = UserID(uuid.UUID(int=1))
_JOINED_PROJECT_ID = ProjectID(uuid.UUID(int=2))
_GROUP_ID_FILTER = ProjectID(uuid.UUID(int=3))
_TEMPLATE_IN_SCOPES = SessionTemplateWithOwnerEmailAndProjectName(
    template=SessionTemplateData(
        id=SessionTemplateID(uuid.UUID(int=10)),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        is_active=True,
        domain_name="default",
        group_id=_JOINED_PROJECT_ID,
        user_uuid=_REQUESTER_ID,
        type=TemplateType.TASK,
        name="in-scopes",
        template={},
    ),
    owner_email="requester@example.com",
    project_name="joined-project",
)
_TEMPLATE_IN_GLOBAL = SessionTemplateWithOwnerEmailAndProjectName(
    template=SessionTemplateData(
        id=SessionTemplateID(uuid.UUID(int=11)),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        is_active=True,
        domain_name="default",
        group_id=None,
        user_uuid=UserID(uuid.UUID(int=20)),
        type=TemplateType.TASK,
        name="in-global",
        template={},
    ),
    owner_email="someone@example.com",
    project_name=None,
)

_STORED_CLUSTER_TEMPLATE = SessionTemplateData(
    id=SessionTemplateID(uuid.UUID(int=12)),
    created_at=datetime(2026, 1, 1, tzinfo=UTC),
    is_active=True,
    domain_name="default",
    group_id=_JOINED_PROJECT_ID,
    user_uuid=_REQUESTER_ID,
    type=TemplateType.CLUSTER,
    name="stored-cluster",
    template={"spec": {"nodes": []}, "metadata": {"name": "stored-cluster"}},
)


def _template_id(name: str) -> SessionTemplateID:
    """The same name always names the same template, so an assertion can restate it."""
    return SessionTemplateID(uuid.uuid5(uuid.NAMESPACE_OID, name))


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
            "requester_uuid": UserID(uuid.uuid4()),
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
        owner_uuid = UserID(uuid.uuid4())
        group_id = ProjectID(uuid.uuid4())
        mock_repo.resolve_owner = AsyncMock(return_value=(owner_uuid, group_id))
        mock_repo.create_task_templates = AsyncMock(return_value=None)

        action = CreateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        result = await service.create_task_template(action)

        items_arg = mock_repo.create_task_templates.call_args[0][1]
        assert len(result.created) == 1
        assert result.created[0].id == items_arg[0]["id"]
        assert result.created[0].user == owner_uuid
        mock_repo.create_task_templates.assert_called_once()

    async def test_batch_creation_multiple_items(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        owner1 = UserID(uuid.uuid4())
        owner2 = UserID(uuid.uuid4())
        group1 = ProjectID(uuid.uuid4())
        group2 = ProjectID(uuid.uuid4())
        default_owner = UserID(uuid.uuid4())
        default_group = ProjectID(uuid.uuid4())
        mock_repo.resolve_owner = AsyncMock(return_value=(default_owner, default_group))
        mock_repo.create_task_templates = AsyncMock(return_value=None)

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
        mock_repo.resolve_owner = AsyncMock(
            return_value=(UserID(uuid.uuid4()), ProjectID(uuid.uuid4()))
        )

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
        mock_repo.resolve_owner = AsyncMock(
            return_value=(UserID(uuid.uuid4()), ProjectID(uuid.uuid4()))
        )

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
        override_owner = UserID(uuid.uuid4())
        override_group = ProjectID(uuid.uuid4())
        mock_repo.resolve_owner = AsyncMock(return_value=(override_owner, override_group))
        mock_repo.create_task_templates = AsyncMock(return_value=None)

        base_action_kwargs["owner_access_key"] = "OVERRIDE_KEY"
        action = CreateTaskTemplateAction(
            **base_action_kwargs,
            items=[TaskTemplateItemInput(template=_make_valid_task_template())],
        )
        result = await service.create_task_template(action)

        mock_repo.resolve_owner.assert_called_once()
        call_kwargs = mock_repo.resolve_owner.call_args
        assert call_kwargs[1]["owner_access_key"] == "OVERRIDE_KEY"
        assert result.created[0].user == override_owner

    async def test_name_from_metadata_when_not_provided(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(
            return_value=(UserID(uuid.uuid4()), ProjectID(uuid.uuid4()))
        )
        mock_repo.create_task_templates = AsyncMock(return_value=None)

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

    async def test_returns_the_stored_template(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_task_template = AsyncMock(return_value=_TEMPLATE_IN_SCOPES.template)

        action = GetTaskTemplateAction(template_id=_TEMPLATE_IN_SCOPES.template.id)
        result = await service.get_task_template(action)

        assert result.template == _TEMPLATE_IN_SCOPES.template
        mock_repo.get_task_template.assert_called_once_with(_TEMPLATE_IN_SCOPES.template.id)

    async def test_nonexistent_id_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_task_template = AsyncMock(return_value=None)

        action = GetTaskTemplateAction(template_id=_template_id("nonexistent"))
        with pytest.raises(SessionTemplateNotFound):
            await service.get_task_template(action)


class TestListTaskTemplatesAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        repo = MagicMock(spec=TemplateRepository)
        repo.joined_project_ids = AsyncMock(return_value=[_JOINED_PROJECT_ID])
        repo.list_templates_in_scopes = AsyncMock(return_value=[_TEMPLATE_IN_SCOPES])
        return repo

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_lists_the_requester_and_their_joined_projects(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        result = await service.list_task_templates(
            ListTaskTemplatesAction(user_uuid=_REQUESTER_ID, group_id_filter=_GROUP_ID_FILTER)
        )

        assert result.entries == [_TEMPLATE_IN_SCOPES]
        mock_repo.list_templates_in_scopes.assert_called_once_with(
            TemplateType.TASK,
            [
                UserSessionTemplateTarget(user_id=_REQUESTER_ID),
                ProjectSessionTemplateTarget(project_id=_JOINED_PROJECT_ID),
            ],
            _GROUP_ID_FILTER,
        )


class TestGlobalListTaskTemplatesAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        repo = MagicMock(spec=TemplateRepository)
        repo.list_templates_in_global = AsyncMock(return_value=[_TEMPLATE_IN_GLOBAL])
        return repo

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_returns_every_template(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        result = await service.global_list_task_templates(GlobalListTaskTemplatesAction())

        assert result.entries == [_TEMPLATE_IN_GLOBAL]
        mock_repo.list_templates_in_global.assert_called_once_with(TemplateType.TASK)


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
            "template_id": _template_id("tmpl-existing"),
            "domain_name": "default",
            "requesting_project": ProjectID(uuid.uuid4()),
            "requester_uuid": UserID(uuid.uuid4()),
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
        mock_repo.resolve_owner = AsyncMock(
            return_value=(UserID(uuid.uuid4()), ProjectID(uuid.uuid4()))
        )
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
        with pytest.raises(SessionTemplateNotFound):
            await service.update_task_template(action)

    async def test_invalid_template_raises_error(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.task_template_exists = AsyncMock(return_value=True)
        mock_repo.resolve_owner = AsyncMock(
            return_value=(UserID(uuid.uuid4()), ProjectID(uuid.uuid4()))
        )

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
        mock_repo.resolve_owner = AsyncMock(
            return_value=(UserID(uuid.uuid4()), ProjectID(uuid.uuid4()))
        )
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

        action = DeleteTaskTemplateAction(template_id=_template_id("tmpl-to-delete"))
        result = await service.delete_task_template(action)

        assert result is not None
        mock_repo.soft_delete_template.assert_called_once_with(
            _template_id("tmpl-to-delete"), TemplateType.TASK
        )

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.task_template_exists = AsyncMock(return_value=False)

        action = DeleteTaskTemplateAction(template_id=_template_id("nonexistent"))
        with pytest.raises(SessionTemplateNotFound):
            await service.delete_task_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.task_template_exists = AsyncMock(return_value=True)
        mock_repo.soft_delete_template = AsyncMock(return_value=0)

        action = DeleteTaskTemplateAction(template_id=_template_id("tmpl-x"))
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
            "requesting_project": ProjectID(uuid.uuid4()),
            "requester_uuid": UserID(uuid.uuid4()),
            "requester_access_key": "AKIAIOSFODNN7EXAMPLE",
            "requester_role": UserRole.USER,
            "requester_domain": "default",
            "owner_access_key": None,
        }

    async def test_valid_cluster_returns_id_and_owner(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        owner_uuid = UserID(uuid.uuid4())
        group_id = ProjectID(uuid.uuid4())
        mock_repo.resolve_owner = AsyncMock(return_value=(owner_uuid, group_id))
        mock_repo.create_cluster_template = AsyncMock(return_value=_template_id("cluster-1"))

        action = CreateClusterTemplateAction(
            **base_action_kwargs,
            template_data=_make_valid_cluster_template(),
        )
        result = await service.create_cluster_template(action)

        assert result.id == _template_id("cluster-1")
        assert result.user == owner_uuid

    async def test_no_master_node_raises_invalid_argument(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
        base_action_kwargs: dict[str, Any],
    ) -> None:
        mock_repo.resolve_owner = AsyncMock(
            return_value=(UserID(uuid.uuid4()), ProjectID(uuid.uuid4()))
        )

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
        mock_repo.resolve_owner = AsyncMock(
            return_value=(UserID(uuid.uuid4()), ProjectID(uuid.uuid4()))
        )

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
        mock_repo.resolve_owner = AsyncMock(
            return_value=(UserID(uuid.uuid4()), ProjectID(uuid.uuid4()))
        )

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

    async def test_returns_the_stored_template(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template = AsyncMock(return_value=_STORED_CLUSTER_TEMPLATE)

        action = GetClusterTemplateAction(template_id=_STORED_CLUSTER_TEMPLATE.id)
        result = await service.get_cluster_template(action)

        assert result.template == _STORED_CLUSTER_TEMPLATE

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.get_cluster_template = AsyncMock(return_value=None)

        action = GetClusterTemplateAction(template_id=_template_id("nonexistent"))
        with pytest.raises(SessionTemplateNotFound):
            await service.get_cluster_template(action)


class TestListClusterTemplatesAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        repo = MagicMock(spec=TemplateRepository)
        repo.joined_project_ids = AsyncMock(return_value=[_JOINED_PROJECT_ID])
        repo.list_templates_in_scopes = AsyncMock(return_value=[_TEMPLATE_IN_SCOPES])
        return repo

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_lists_the_requester_and_their_joined_projects(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        result = await service.list_cluster_templates(
            ListClusterTemplatesAction(user_uuid=_REQUESTER_ID, group_id_filter=_GROUP_ID_FILTER)
        )

        assert result.entries == [_TEMPLATE_IN_SCOPES]
        mock_repo.list_templates_in_scopes.assert_called_once_with(
            TemplateType.CLUSTER,
            [
                UserSessionTemplateTarget(user_id=_REQUESTER_ID),
                ProjectSessionTemplateTarget(project_id=_JOINED_PROJECT_ID),
            ],
            _GROUP_ID_FILTER,
        )


class TestGlobalListClusterTemplatesAction:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        repo = MagicMock(spec=TemplateRepository)
        repo.list_templates_in_global = AsyncMock(return_value=[_TEMPLATE_IN_GLOBAL])
        return repo

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> TemplateService:
        return TemplateService(repository=mock_repo)

    async def test_returns_every_template(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        result = await service.global_list_cluster_templates(GlobalListClusterTemplatesAction())

        assert result.entries == [_TEMPLATE_IN_GLOBAL]
        mock_repo.list_templates_in_global.assert_called_once_with(TemplateType.CLUSTER)


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
            template_id=_template_id("cluster-1"),
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
            template_id=_template_id("nonexistent"),
            template_data=_make_valid_cluster_template(),
        )
        with pytest.raises(SessionTemplateNotFound):
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
            template_id=_template_id("cluster-1"),
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
            template_id=_template_id("cluster-1"),
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

        action = DeleteClusterTemplateAction(template_id=_template_id("cluster-to-delete"))
        result = await service.delete_cluster_template(action)

        assert result is not None
        mock_repo.soft_delete_template.assert_called_once_with(
            _template_id("cluster-to-delete"), TemplateType.CLUSTER
        )

    async def test_nonexistent_raises_not_found(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.cluster_template_exists = AsyncMock(return_value=False)

        action = DeleteClusterTemplateAction(template_id=_template_id("nonexistent"))
        with pytest.raises(SessionTemplateNotFound):
            await service.delete_cluster_template(action)

    async def test_rowcount_not_one_raises_db_operation_failed(
        self,
        service: TemplateService,
        mock_repo: MagicMock,
    ) -> None:
        mock_repo.cluster_template_exists = AsyncMock(return_value=True)
        mock_repo.soft_delete_template = AsyncMock(return_value=0)

        action = DeleteClusterTemplateAction(template_id=_template_id("cluster-x"))
        with pytest.raises(DBOperationFailed):
            await service.delete_cluster_template(action)
