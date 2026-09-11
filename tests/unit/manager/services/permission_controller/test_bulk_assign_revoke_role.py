"""Unit tests for bulk assign/revoke role service methods."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.permission.role import (
    BulkRoleAssignmentResultData,
    BulkRoleRevocationFailure,
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
    UserRoleAssignmentData,
    UserRoleRevocationData,
)
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


class TestBulkAssignRole:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.bulk_assign_role = AsyncMock()
        return repository

    @pytest.fixture
    def service(self, mock_repository: PermissionControllerRepository) -> RbacRoleService:
        return RbacRoleService(mock_repository, MagicMock())

    async def test_bulk_assign_all_succeed(
        self,
        service: RbacRoleService,
        mock_repository: MagicMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        successes = [
            UserRoleAssignmentData(id=uuid.uuid4(), user_id=uid, role_id=role_id, granted_by=None)
            for uid in user_ids
        ]
        mock_repository.bulk_assign_role.return_value = BulkRoleAssignmentResultData(
            successes=successes, failures=[]
        )

        action = BulkAssignRoleAction(
            role_id=RoleID(role_id), user_ids=[UserID(uid) for uid in user_ids]
        )
        result = await service.bulk_assign_role(action)

        mock_repository.bulk_assign_role.assert_called_once_with(
            RoleID(role_id), [UserID(uid) for uid in user_ids], None
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

        action = BulkAssignRoleAction(role_id=RoleID(uuid.uuid4()), user_ids=[])
        result = await service.bulk_assign_role(action)

        assert len(result.data.successes) == 0
        assert len(result.data.failures) == 0


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
            UserRoleRevocationData(user_role_id=uuid.uuid4(), user_id=uid, role_id=role_id)
            for uid in user_ids
        ]
        mock_repository.bulk_revoke_role.return_value = BulkRoleRevocationResultData(
            successes=successes, failures=[]
        )

        input_data = BulkUserRoleRevocationInput(role_id=role_id, user_ids=user_ids)
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
                UserRoleRevocationData(
                    user_role_id=uuid.uuid4(),
                    user_id=user_ids[0],
                    role_id=role_id,
                )
            ],
            failures=[BulkRoleRevocationFailure(user_id=user_ids[1], message="Role not assigned")],
        )

        input_data = BulkUserRoleRevocationInput(role_id=role_id, user_ids=user_ids)
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
                BulkRoleRevocationFailure(user_id=uid, message="Role not assigned")
                for uid in user_ids
            ],
        )

        input_data = BulkUserRoleRevocationInput(role_id=role_id, user_ids=user_ids)
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

        input_data = BulkUserRoleRevocationInput(role_id=role_id, user_ids=[])
        action = BulkRevokeRoleAction(input=input_data)
        result = await service.bulk_revoke_role(action)

        assert len(result.data.successes) == 0
        assert len(result.data.failures) == 0
