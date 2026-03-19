"""Tests for adminBulkAssignRole and adminBulkRevokeRole GraphQL resolvers."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkAssignRoleResultPayload,
    BulkRevokeRoleResultPayload,
    BulkRoleOperationFailureInfo,
    RoleAssignmentNode,
)
from ai.backend.manager.api.gql.rbac.resolver import role as role_resolver
from ai.backend.manager.api.gql.rbac.types import (
    BulkAssignRoleInputGQL,
    BulkAssignRolePayloadGQL,
    BulkRevokeRoleInputGQL,
    BulkRevokeRolePayloadGQL,
)


class TestAdminBulkAssignRole:
    @pytest.fixture(autouse=True)
    def _bypass_admin_check(self) -> Generator[None]:
        with patch("ai.backend.manager.api.gql.rbac.resolver.role.check_admin_only"):
            yield

    @pytest.fixture
    def mock_adapter(self) -> AsyncMock:
        adapter = AsyncMock()
        adapter.bulk_assign_role = AsyncMock()
        return adapter

    @pytest.fixture
    def mock_info(self, mock_adapter: AsyncMock) -> MagicMock:
        info = MagicMock()
        info.context.adapters.rbac = mock_adapter
        return info

    async def test_returns_payload_with_assigned_and_failed(
        self,
        mock_info: MagicMock,
        mock_adapter: AsyncMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_id_success = uuid.uuid4()
        user_id_fail = uuid.uuid4()

        mock_adapter.bulk_assign_role.return_value = BulkAssignRoleResultPayload(
            successes=[
                RoleAssignmentNode(
                    id=uuid.uuid4(),
                    user_id=user_id_success,
                    role_id=role_id,
                    granted_by=None,
                    granted_at=datetime(2025, 1, 1, tzinfo=UTC),
                )
            ],
            failures=[
                BulkRoleOperationFailureInfo(user_id=user_id_fail, message="Role already assigned")
            ],
        )

        input_data = BulkAssignRoleInputGQL(
            role_id=role_id, user_ids=[user_id_success, user_id_fail]
        )

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
        mock_adapter: AsyncMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4()]

        mock_adapter.bulk_assign_role.return_value = BulkAssignRoleResultPayload(
            successes=[], failures=[]
        )

        input_data = BulkAssignRoleInputGQL(role_id=role_id, user_ids=user_ids)

        resolver_fn = role_resolver.admin_bulk_assign_role.base_resolver
        await resolver_fn(mock_info, input_data)

        mock_adapter.bulk_assign_role.assert_called_once()


class TestAdminBulkRevokeRole:
    @pytest.fixture(autouse=True)
    def _bypass_admin_check(self) -> Generator[None]:
        with patch("ai.backend.manager.api.gql.rbac.resolver.role.check_admin_only"):
            yield

    @pytest.fixture
    def mock_adapter(self) -> AsyncMock:
        adapter = AsyncMock()
        adapter.bulk_revoke_role = AsyncMock()
        return adapter

    @pytest.fixture
    def mock_info(self, mock_adapter: AsyncMock) -> MagicMock:
        info = MagicMock()
        info.context.adapters.rbac = mock_adapter
        return info

    async def test_returns_payload_with_revoked_and_failed(
        self,
        mock_info: MagicMock,
        mock_adapter: AsyncMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_id_success = uuid.uuid4()
        user_id_fail = uuid.uuid4()

        mock_adapter.bulk_revoke_role.return_value = BulkRevokeRoleResultPayload(
            successes=[
                RoleAssignmentNode(
                    id=uuid.uuid4(),
                    user_id=user_id_success,
                    role_id=role_id,
                    granted_by=None,
                    granted_at=datetime(2025, 1, 1, tzinfo=UTC),
                )
            ],
            failures=[
                BulkRoleOperationFailureInfo(user_id=user_id_fail, message="Role not assigned")
            ],
        )

        input_data = BulkRevokeRoleInputGQL(
            role_id=role_id, user_ids=[user_id_success, user_id_fail]
        )

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
        mock_adapter: AsyncMock,
    ) -> None:
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4(), uuid.uuid4()]

        mock_adapter.bulk_revoke_role.return_value = BulkRevokeRoleResultPayload(
            successes=[], failures=[]
        )

        input_data = BulkRevokeRoleInputGQL(role_id=role_id, user_ids=user_ids)

        resolver_fn = role_resolver.admin_bulk_revoke_role.base_resolver
        await resolver_fn(mock_info, input_data)

        mock_adapter.bulk_revoke_role.assert_called_once()
