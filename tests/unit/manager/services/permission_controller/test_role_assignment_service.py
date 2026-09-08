"""Tests for RbacRoleService assign/revoke role with project binding."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
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
from ai.backend.manager.services.rbac.actions.role.assign import AssignRoleAction
from ai.backend.manager.services.rbac.actions.role.bulk_assign import (
    BulkAssignRoleAction,
)
from ai.backend.manager.services.rbac.actions.role.revoke import RevokeRoleAction
from ai.backend.manager.services.rbac.service import RbacRoleService


@pytest.fixture
def mock_repository() -> MagicMock:
    repo = MagicMock()
    repo.assign_role = AsyncMock()
    repo.revoke_role = AsyncMock()
    repo.bulk_assign_role = AsyncMock()
    return repo


@pytest.fixture
def mock_roster_repository() -> MagicMock:
    repo = MagicMock()
    repo.join_member = AsyncMock()
    repo.leave_member = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repository: MagicMock, mock_roster_repository: MagicMock) -> RbacRoleService:
    return RbacRoleService(mock_repository, mock_roster_repository)


class TestAssignRoleWithProject:
    async def test_assign_with_project_id_enrolls(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
        mock_roster_repository: MagicMock,
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

        mock_roster_repository.join_member.assert_called_once_with(
            ProjectID(project_id), UserID(user_id)
        )
        mock_repository.assign_role.assert_called_once()

    async def test_assign_without_project_id_skips_bind(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
        mock_roster_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        mock_repository.assign_role.return_value = UserRoleAssignmentData(
            id=uuid.uuid4(), user_id=user_id, role_id=role_id
        )

        action = AssignRoleAction(input=UserRoleAssignmentInput(user_id=user_id, role_id=role_id))
        await service.assign_role(action)

        mock_roster_repository.join_member.assert_not_called()


class TestRevokeRoleWithProject:
    async def test_revoke_with_zero_remaining_calls_unbind(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
        mock_roster_repository: MagicMock,
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

        mock_roster_repository.leave_member.assert_called_once_with(
            ProjectID(project_id), UserID(user_id)
        )

    async def test_revoke_with_nonzero_remaining_skips_unbind(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
        mock_roster_repository: MagicMock,
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

        mock_roster_repository.leave_member.assert_not_called()

    async def test_revoke_global_role_skips_unbind(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
        mock_roster_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        mock_repository.revoke_role.return_value = RoleRevocationResult(
            user_role_id=uuid.uuid4(),
        )

        action = RevokeRoleAction(input=UserRoleRevocationInput(user_id=user_id, role_id=role_id))
        await service.revoke_role(action)

        mock_roster_repository.leave_member.assert_not_called()


class TestBulkAssignRoleWithProject:
    async def test_bulk_assign_with_project_id_calls_bind_for_each_user(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
        mock_roster_repository: MagicMock,
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

        assert mock_roster_repository.join_member.call_count == 2
        for uid in user_ids:
            mock_roster_repository.join_member.assert_any_call(ProjectID(project_id), UserID(uid))

    async def test_bulk_assign_without_project_id_skips_bind(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
        mock_roster_repository: MagicMock,
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

        mock_roster_repository.join_member.assert_not_called()
