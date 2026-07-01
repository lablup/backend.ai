"""Tests for PermissionControllerService assign/revoke role with project binding."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.permission.role import (
    BulkRoleAssignmentResultData,
    ProjectRoleCount,
    RoleRevocationResult,
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.permission_controller.creators import UserRoleCreatorSpec
from ai.backend.manager.services.permission_contoller.actions.assign_role import AssignRoleAction
from ai.backend.manager.services.permission_contoller.actions.bulk_assign_role import (
    BulkAssignRoleAction,
)
from ai.backend.manager.services.permission_contoller.actions.revoke_role import RevokeRoleAction
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService


@pytest.fixture
def mock_repository() -> MagicMock:
    repo = MagicMock()
    repo.assign_role = AsyncMock()
    repo.revoke_role = AsyncMock()
    repo.bulk_assign_role = AsyncMock()
    return repo


@pytest.fixture
def mock_group_repository() -> MagicMock:
    repo = MagicMock()
    repo.bind_user_to_project = AsyncMock()
    repo.unbind_user_from_project = AsyncMock()
    return repo


@pytest.fixture
def service(
    mock_repository: MagicMock, mock_group_repository: MagicMock
) -> PermissionControllerService:
    return PermissionControllerService(
        repository=mock_repository,
        group_repository=mock_group_repository,
        rbac_action_registry=[],
    )


class TestAssignRoleWithProject:
    async def test_assign_with_project_id_calls_bind(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        project_id = uuid.uuid4()
        mock_repository.assign_role.return_value = UserRoleAssignmentData(
            id=uuid.uuid4(), user_id=user_id, role_id=role_id
        )

        action = AssignRoleAction(
            input=UserRoleAssignmentInput(user_id=user_id, role_id=role_id, project_id=project_id)
        )
        await service.assign_role(action)

        mock_group_repository.bind_user_to_project.assert_called_once_with(user_id, project_id)
        mock_repository.assign_role.assert_called_once()

    async def test_assign_without_project_id_skips_bind(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        mock_repository.assign_role.return_value = UserRoleAssignmentData(
            id=uuid.uuid4(), user_id=user_id, role_id=role_id
        )

        action = AssignRoleAction(input=UserRoleAssignmentInput(user_id=user_id, role_id=role_id))
        await service.assign_role(action)

        mock_group_repository.bind_user_to_project.assert_not_called()


class TestRevokeRoleWithProject:
    async def test_revoke_with_zero_remaining_calls_unbind(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        project_id = uuid.uuid4()
        mock_repository.revoke_role.return_value = RoleRevocationResult(
            user_role_id=uuid.uuid4(),
            project_remaining_roles=[ProjectRoleCount(project_id=project_id, remaining_count=0)],
        )

        action = RevokeRoleAction(input=UserRoleRevocationInput(user_id=user_id, role_id=role_id))
        await service.revoke_role(action)

        mock_group_repository.unbind_user_from_project.assert_called_once_with(user_id, project_id)

    async def test_revoke_with_nonzero_remaining_skips_unbind(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        project_id = uuid.uuid4()
        mock_repository.revoke_role.return_value = RoleRevocationResult(
            user_role_id=uuid.uuid4(),
            project_remaining_roles=[ProjectRoleCount(project_id=project_id, remaining_count=1)],
        )

        action = RevokeRoleAction(input=UserRoleRevocationInput(user_id=user_id, role_id=role_id))
        await service.revoke_role(action)

        mock_group_repository.unbind_user_from_project.assert_not_called()

    async def test_revoke_global_role_skips_unbind(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        mock_repository.revoke_role.return_value = RoleRevocationResult(
            user_role_id=uuid.uuid4(),
        )

        action = RevokeRoleAction(input=UserRoleRevocationInput(user_id=user_id, role_id=role_id))
        await service.revoke_role(action)

        mock_group_repository.unbind_user_from_project.assert_not_called()


class TestBulkAssignRoleWithProject:
    async def test_bulk_assign_with_project_id_calls_bind_for_each_user(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4()]
        project_id = uuid.uuid4()
        mock_repository.bulk_assign_role.return_value = BulkRoleAssignmentResultData(
            successes=[
                UserRoleAssignmentData(id=uuid.uuid4(), user_id=uid, role_id=role_id)
                for uid in user_ids
            ],
            failures=[],
        )

        specs = [UserRoleCreatorSpec(user_id=uid, role_id=role_id) for uid in user_ids]
        action = BulkAssignRoleAction(
            bulk_creator=BulkCreator[UserRoleRow](specs=specs), project_id=project_id
        )
        await service.bulk_assign_role(action)

        assert mock_group_repository.bind_user_to_project.call_count == 2
        for uid in user_ids:
            mock_group_repository.bind_user_to_project.assert_any_call(uid, project_id)

    async def test_bulk_assign_without_project_id_skips_bind(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_repository.bulk_assign_role.return_value = BulkRoleAssignmentResultData(
            successes=[
                UserRoleAssignmentData(id=uuid.uuid4(), user_id=uid, role_id=role_id)
                for uid in user_ids
            ],
            failures=[],
        )

        specs = [UserRoleCreatorSpec(user_id=uid, role_id=role_id) for uid in user_ids]
        action = BulkAssignRoleAction(bulk_creator=BulkCreator[UserRoleRow](specs=specs))
        await service.bulk_assign_role(action)

        mock_group_repository.bind_user_to_project.assert_not_called()
