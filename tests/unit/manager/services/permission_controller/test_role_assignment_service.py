"""Tests for RbacRoleService assign/revoke role with project binding."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    BulkRoleAssignmentResultData,
    ProjectRoleCount,
    RoleRevocationResult,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.repositories.ops.v2.roster.write import (
    RosterJoinFailure,
    RosterJoinResult,
)
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
    repo.join_each = AsyncMock()
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
        mock_repository.assign_role.return_value = AssignedUserData(
            id=uuid.uuid4(),
            user_id=UserID(user_id),
            role_id=RoleID(role_id),
            granted_by=None,
            granted_at=datetime.now(tz=UTC),
        )

        action = AssignRoleAction(
            input=UserRoleAssignmentInput(
                user_id=UserID(user_id),
                role_id=RoleID(role_id),
                granted_by=UserID(uuid.uuid4()),
                project_id=ProjectID(project_id),
            )
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
        mock_repository.assign_role.return_value = AssignedUserData(
            id=uuid.uuid4(),
            user_id=UserID(user_id),
            role_id=RoleID(role_id),
            granted_by=None,
            granted_at=datetime.now(tz=UTC),
        )

        action = AssignRoleAction(
            input=UserRoleAssignmentInput(
                user_id=UserID(user_id), role_id=RoleID(role_id), granted_by=UserID(uuid.uuid4())
            )
        )
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
            revoked=AssignedUserData(
                id=uuid.uuid4(),
                user_id=UserID(user_id),
                role_id=RoleID(role_id),
                granted_by=None,
                granted_at=datetime.now(tz=UTC),
            ),
            project_remaining_roles=[
                ProjectRoleCount(project_id=ProjectID(project_id), remaining_count=0)
            ],
        )

        action = RevokeRoleAction(
            input=UserRoleRevocationInput(user_id=UserID(user_id), role_id=RoleID(role_id))
        )
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
            revoked=AssignedUserData(
                id=uuid.uuid4(),
                user_id=UserID(user_id),
                role_id=RoleID(role_id),
                granted_by=None,
                granted_at=datetime.now(tz=UTC),
            ),
            project_remaining_roles=[
                ProjectRoleCount(project_id=ProjectID(project_id), remaining_count=1)
            ],
        )

        action = RevokeRoleAction(
            input=UserRoleRevocationInput(user_id=UserID(user_id), role_id=RoleID(role_id))
        )
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
            revoked=AssignedUserData(
                id=uuid.uuid4(),
                user_id=UserID(user_id),
                role_id=RoleID(role_id),
                granted_by=None,
                granted_at=datetime.now(tz=UTC),
            ),
        )

        action = RevokeRoleAction(
            input=UserRoleRevocationInput(user_id=UserID(user_id), role_id=RoleID(role_id))
        )
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
                AssignedUserData(
                    id=uuid.uuid4(),
                    user_id=UserID(uid),
                    role_id=RoleID(role_id),
                    granted_by=None,
                    granted_at=datetime.now(tz=UTC),
                )
                for uid in user_ids
            ],
            failures=[],
        )

        action = BulkAssignRoleAction(
            role_id=RoleID(role_id),
            user_ids=[UserID(uid) for uid in user_ids],
            granted_by=UserID(uuid.uuid4()),
            project_id=ProjectID(project_id),
        )
        mock_roster_repository.join_each.return_value = RosterJoinResult(
            joined=[UserID(uid) for uid in user_ids]
        )
        await service.bulk_assign_role(action)

        mock_roster_repository.join_each.assert_called_once_with(
            ProjectID(project_id), [UserID(uid) for uid in user_ids]
        )

    async def test_bulk_assign_fails_only_the_user_who_cannot_join(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
        mock_roster_repository: MagicMock,
    ) -> None:
        role_id = RoleID(uuid.uuid4())
        project_id = ProjectID(uuid.uuid4())
        refused, joined = UserID(uuid.uuid4()), UserID(uuid.uuid4())
        granted = AssignedUserData(
            id=uuid.uuid4(),
            user_id=joined,
            role_id=role_id,
            granted_by=None,
            granted_at=datetime.now(tz=UTC),
        )

        mock_roster_repository.join_each.return_value = RosterJoinResult(
            joined=[joined],
            failures=[RosterJoinFailure(user_id=refused, message="cannot join")],
        )
        mock_repository.bulk_assign_role.return_value = BulkRoleAssignmentResultData(
            successes=[granted], failures=[]
        )

        result = await service.bulk_assign_role(
            BulkAssignRoleAction(
                role_id=role_id,
                user_ids=[refused, joined],
                granted_by=UserID(uuid.uuid4()),
                project_id=project_id,
            )
        )

        mock_repository.bulk_assign_role.assert_called_once_with(role_id, [joined], ANY)
        assert result.data.successes == [granted]
        assert [f.user_id for f in result.data.failures] == [refused]

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
                AssignedUserData(
                    id=uuid.uuid4(),
                    user_id=UserID(uid),
                    role_id=RoleID(role_id),
                    granted_by=None,
                    granted_at=datetime.now(tz=UTC),
                )
                for uid in user_ids
            ],
            failures=[],
        )

        action = BulkAssignRoleAction(
            role_id=RoleID(role_id),
            user_ids=[UserID(uid) for uid in user_ids],
            granted_by=UserID(uuid.uuid4()),
        )
        await service.bulk_assign_role(action)

        mock_roster_repository.join_each.assert_not_called()
