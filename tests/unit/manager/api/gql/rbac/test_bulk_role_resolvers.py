"""Tests for adminBulkAssignRole and adminBulkRevokeRole GraphQL resolvers."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.api.gql.rbac.resolver import role as role_resolver
from ai.backend.manager.api.gql.rbac.types import (
    BulkAssignRoleInput,
    BulkAssignRolePayloadGQL,
    BulkRevokeRoleInput,
    BulkRevokeRolePayloadGQL,
)
from ai.backend.manager.data.permission.role import (
    BulkRoleAssignmentFailure,
    BulkRoleAssignmentResultData,
    BulkRoleRevocationFailure,
    BulkRoleRevocationResultData,
    UserRoleAssignmentData,
    UserRoleRevocationData,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_assign_role import (
    BulkAssignRoleActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.bulk_revoke_role import (
    BulkRevokeRoleActionResult,
)


class TestAdminBulkAssignRole:
    @pytest.fixture
    def mock_processor(self) -> AsyncMock:
        processor = AsyncMock()
        processor.wait_for_complete = AsyncMock()
        return processor

    @pytest.fixture
    def mock_info(self, mock_processor: AsyncMock) -> MagicMock:
        info = MagicMock()
        info.context.processors.permission_controller.bulk_assign_role = mock_processor
        return info

    async def test_returns_payload_with_assigned_and_failed(
        self,
        mock_info: MagicMock,
        mock_processor: AsyncMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_id_success = uuid.uuid4()
        user_id_fail = uuid.uuid4()

        mock_processor.wait_for_complete.return_value = BulkAssignRoleActionResult(
            data=BulkRoleAssignmentResultData(
                successes=[
                    UserRoleAssignmentData(
                        id=uuid.uuid4(),
                        user_id=user_id_success,
                        role_id=role_id,
                        granted_by=None,
                    )
                ],
                failures=[
                    BulkRoleAssignmentFailure(user_id=user_id_fail, message="Role already assigned")
                ],
            )
        )

        input_data = BulkAssignRoleInput(role_id=role_id, user_ids=[user_id_success, user_id_fail])

        resolver_fn = role_resolver.admin_bulk_assign_role.base_resolver
        result = await resolver_fn(mock_info, input_data)

        assert isinstance(result, BulkAssignRolePayloadGQL)
        assert len(result.assigned) == 1
        assert result.assigned[0].user_id == user_id_success
        assert len(result.failed) == 1
        assert result.failed[0].user_id == user_id_fail
        assert result.failed[0].message == "Role already assigned"

    async def test_constructs_action_from_input(
        self,
        mock_info: MagicMock,
        mock_processor: AsyncMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4()]

        mock_processor.wait_for_complete.return_value = BulkAssignRoleActionResult(
            data=BulkRoleAssignmentResultData(successes=[], failures=[])
        )

        input_data = BulkAssignRoleInput(role_id=role_id, user_ids=user_ids)

        resolver_fn = role_resolver.admin_bulk_assign_role.base_resolver
        await resolver_fn(mock_info, input_data)

        mock_processor.wait_for_complete.assert_called_once()
        action = mock_processor.wait_for_complete.call_args[0][0]
        specs = action.bulk_creator.specs
        assert len(specs) == len(user_ids)
        for spec, uid in zip(specs, user_ids, strict=True):
            assert spec.user_id == uid
            assert spec.role_id == role_id


class TestAdminBulkRevokeRole:
    @pytest.fixture
    def mock_processor(self) -> AsyncMock:
        processor = AsyncMock()
        processor.wait_for_complete = AsyncMock()
        return processor

    @pytest.fixture
    def mock_info(self, mock_processor: AsyncMock) -> MagicMock:
        info = MagicMock()
        info.context.processors.permission_controller.bulk_revoke_role = mock_processor
        return info

    async def test_returns_payload_with_revoked_and_failed(
        self,
        mock_info: MagicMock,
        mock_processor: AsyncMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_id_success = uuid.uuid4()
        user_id_fail = uuid.uuid4()

        mock_processor.wait_for_complete.return_value = BulkRevokeRoleActionResult(
            data=BulkRoleRevocationResultData(
                successes=[
                    UserRoleRevocationData(
                        user_role_id=uuid.uuid4(),
                        user_id=user_id_success,
                        role_id=role_id,
                    )
                ],
                failures=[
                    BulkRoleRevocationFailure(user_id=user_id_fail, message="Role not assigned")
                ],
            )
        )

        input_data = BulkRevokeRoleInput(role_id=role_id, user_ids=[user_id_success, user_id_fail])

        resolver_fn = role_resolver.admin_bulk_revoke_role.base_resolver
        result = await resolver_fn(mock_info, input_data)

        assert isinstance(result, BulkRevokeRolePayloadGQL)
        assert len(result.revoked) == 1
        assert result.revoked[0].user_id == user_id_success
        assert len(result.failed) == 1
        assert result.failed[0].user_id == user_id_fail
        assert result.failed[0].message == "Role not assigned"

    async def test_constructs_action_from_input(
        self,
        mock_info: MagicMock,
        mock_processor: AsyncMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4()]

        mock_processor.wait_for_complete.return_value = BulkRevokeRoleActionResult(
            data=BulkRoleRevocationResultData(successes=[], failures=[])
        )

        input_data = BulkRevokeRoleInput(role_id=role_id, user_ids=user_ids)

        resolver_fn = role_resolver.admin_bulk_revoke_role.base_resolver
        await resolver_fn(mock_info, input_data)

        mock_processor.wait_for_complete.assert_called_once()
        action = mock_processor.wait_for_complete.call_args[0][0]
        assert action.input.role_id == role_id
        assert action.input.user_ids == user_ids
