"""Unit tests for bulk assign/revoke role service methods."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    BulkRoleAssignmentResultData,
    BulkRoleRevocationFailure,
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
)
from ai.backend.manager.errors.permission import RoleNotFound
from ai.backend.manager.services.rbac.actions.role.bulk_assign import (
    BulkAssignRoleAction,
)
from ai.backend.manager.services.rbac.actions.role.bulk_revoke import (
    BulkRevokeRoleAction,
)
from ai.backend.manager.services.rbac.service import RbacRoleService

if TYPE_CHECKING:
    from ai.backend.manager.repositories.permission_controller.repository import (
        PermissionControllerRepository,
    )
    from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository


class TestBulkAssignRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.bulk_assign_role = AsyncMock()
        return repository

    @pytest.fixture
    def mock_roster_repository(self) -> MagicMock:
        roster_repository = MagicMock()
        roster_repository.join_each = AsyncMock()
        return roster_repository

    @pytest.fixture
    def service(
        self,
        mock_repository: PermissionControllerRepository,
        mock_roster_repository: RbacRosterRepository,
    ) -> RbacRoleService:
        return RbacRoleService(mock_repository, mock_roster_repository)

    async def test_bulk_assign_all_succeed(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        successes = [
            AssignedUserData(
                id=uuid.uuid4(),
                user_id=UserID(uid),
                role_id=RoleID(role_id),
                granted_by=None,
                granted_at=datetime.now(tz=UTC),
            )
            for uid in user_ids
        ]
        mock_repository.bulk_assign_role.return_value = BulkRoleAssignmentResultData(
            successes=successes, failures=[]
        )

        granted_by = UserID(uuid.uuid4())
        action = BulkAssignRoleAction(
            role_id=RoleID(role_id),
            user_ids=[UserID(uid) for uid in user_ids],
            granted_by=granted_by,
        )
        result = await service.bulk_assign_role(action)

        mock_repository.bulk_assign_role.assert_called_once_with(
            RoleID(role_id), [UserID(uid) for uid in user_ids], granted_by
        )
        assert len(result.data.successes) == 3
        assert len(result.data.failures) == 0

    async def test_bulk_assign_empty_user_ids(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.bulk_assign_role.return_value = BulkRoleAssignmentResultData(
            successes=[], failures=[]
        )

        action = BulkAssignRoleAction(
            role_id=RoleID(uuid.uuid4()), user_ids=[], granted_by=UserID(uuid.uuid4())
        )
        result = await service.bulk_assign_role(action)

        assert len(result.data.successes) == 0
        assert len(result.data.failures) == 0

    async def test_unknown_role_with_a_project_is_refused_before_anyone_joins(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
        mock_roster_repository: MagicMock,
    ) -> None:
        mock_repository.get_role = AsyncMock(return_value=None)

        action = BulkAssignRoleAction(
            role_id=RoleID(uuid.uuid4()),
            user_ids=[UserID(uuid.uuid4())],
            granted_by=UserID(uuid.uuid4()),
            project_id=ProjectID(uuid.uuid4()),
        )
        with pytest.raises(RoleNotFound):
            await service.bulk_assign_role(action)

        mock_roster_repository.join_each.assert_not_called()
        mock_repository.bulk_assign_role.assert_not_called()


class TestBulkRevokeRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.bulk_revoke_role = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: PermissionControllerRepository) -> RbacRoleService:
        return RbacRoleService(mock_repository, MagicMock())

    async def test_bulk_revoke_all_succeed(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        successes = [
            AssignedUserData(
                id=uuid.uuid4(),
                user_id=UserID(uid),
                role_id=RoleID(role_id),
                granted_by=None,
                granted_at=datetime.now(tz=UTC),
            )
            for uid in user_ids
        ]
        mock_repository.bulk_revoke_role.return_value = BulkRoleRevocationResultData(
            successes=successes, failures=[]
        )

        input_data = BulkUserRoleRevocationInput(
            role_id=RoleID(role_id), user_ids=[UserID(uid) for uid in user_ids]
        )
        action = BulkRevokeRoleAction(input=input_data)
        result = await service.bulk_revoke_role(action)

        mock_repository.bulk_revoke_role.assert_called_once_with(input_data)
        assert len(result.data.successes) == 3
        assert len(result.data.failures) == 0

    async def test_bulk_revoke_partial_failure(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_repository.bulk_revoke_role.return_value = BulkRoleRevocationResultData(
            successes=[
                AssignedUserData(
                    id=uuid.uuid4(),
                    user_id=UserID(user_ids[0]),
                    role_id=RoleID(role_id),
                    granted_by=None,
                    granted_at=datetime.now(tz=UTC),
                )
            ],
            failures=[
                BulkRoleRevocationFailure(user_id=UserID(user_ids[1]), message="Role not assigned")
            ],
        )

        input_data = BulkUserRoleRevocationInput(
            role_id=RoleID(role_id), user_ids=[UserID(uid) for uid in user_ids]
        )
        action = BulkRevokeRoleAction(input=input_data)
        result = await service.bulk_revoke_role(action)

        assert len(result.data.successes) == 1
        assert len(result.data.failures) == 1
        assert result.data.failures[0].user_id == user_ids[1]

    async def test_bulk_revoke_all_fail(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_repository.bulk_revoke_role.return_value = BulkRoleRevocationResultData(
            successes=[],
            failures=[
                BulkRoleRevocationFailure(user_id=UserID(uid), message="Role not assigned")
                for uid in user_ids
            ],
        )

        input_data = BulkUserRoleRevocationInput(
            role_id=RoleID(role_id), user_ids=[UserID(uid) for uid in user_ids]
        )
        action = BulkRevokeRoleAction(input=input_data)
        result = await service.bulk_revoke_role(action)

        assert len(result.data.successes) == 0
        assert len(result.data.failures) == 2

    async def test_bulk_revoke_empty_user_ids(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        mock_repository.bulk_revoke_role.return_value = BulkRoleRevocationResultData(
            successes=[], failures=[]
        )

        input_data = BulkUserRoleRevocationInput(role_id=RoleID(role_id), user_ids=[])
        action = BulkRevokeRoleAction(input=input_data)
        result = await service.bulk_revoke_role(action)

        assert len(result.data.successes) == 0
        assert len(result.data.failures) == 0
