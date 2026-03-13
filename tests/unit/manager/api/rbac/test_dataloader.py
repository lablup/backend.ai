"""Tests for RBAC GraphQL DataLoader utilities."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.manager.api.gql.data_loader.rbac.loader import (
    load_assignments_by_role_ids,
)
from ai.backend.manager.data.permission.role import AssignedUserData


class TestLoadAssignmentsByRoleIds:
    """Tests for load_assignments_by_role_ids function."""

    @staticmethod
    def create_mock_assignment(role_id: uuid.UUID, user_id: uuid.UUID) -> MagicMock:
        mock = MagicMock(spec=AssignedUserData)
        mock.role_id = role_id
        mock.user_id = user_id
        return mock

    @staticmethod
    def create_mock_processor(assignments: list[MagicMock]) -> MagicMock:
        mock_processor = MagicMock()
        mock_action_result = MagicMock()
        mock_action_result.result = MagicMock()
        mock_action_result.result.items = assignments
        mock_processor.search_users_assigned_to_role.wait_for_complete = AsyncMock(
            return_value=mock_action_result
        )
        return mock_processor

    async def test_empty_ids_returns_empty_list(self) -> None:
        # Given
        mock_processor = MagicMock()

        # When
        result = await load_assignments_by_role_ids(mock_processor, [])

        # Then
        assert result == []
        mock_processor.search_users_assigned_to_role.wait_for_complete.assert_not_called()

    async def test_returns_assignments_grouped_by_role(self) -> None:
        # Given
        role1_id, role2_id, role3_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        user1_id, user2_id, user3_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        # Create assignments for different roles
        assignment_r1_u1 = self.create_mock_assignment(role1_id, user1_id)
        assignment_r1_u2 = self.create_mock_assignment(role1_id, user2_id)
        assignment_r2_u3 = self.create_mock_assignment(role2_id, user3_id)

        # DB returns in arbitrary order
        mock_processor = self.create_mock_processor([
            assignment_r2_u3,
            assignment_r1_u1,
            assignment_r1_u2,
        ])

        # When - request in different order: role2, role1, role3
        result = await load_assignments_by_role_ids(mock_processor, [role2_id, role1_id, role3_id])

        # Then - results preserve input order
        assert len(result) == 3
        assert result[0] == [assignment_r2_u3]  # role2 assignments
        assert result[1] == [assignment_r1_u1, assignment_r1_u2]  # role1 assignments
        assert result[2] == []  # role3 has no assignments

    async def test_returns_empty_list_for_roles_with_no_assignments(self) -> None:
        # Given
        existing_role_id = uuid.uuid4()
        no_assignment_role_id = uuid.uuid4()
        user_id = uuid.uuid4()

        assignment = self.create_mock_assignment(existing_role_id, user_id)
        mock_processor = self.create_mock_processor([assignment])

        # When
        result = await load_assignments_by_role_ids(
            mock_processor, [existing_role_id, no_assignment_role_id]
        )

        # Then
        assert len(result) == 2
        assert result[0] == [assignment]
        assert result[1] == []  # Empty list, not None

    async def test_preserves_input_order_regardless_of_db_order(self) -> None:
        # Given
        role_ids = [uuid.uuid4() for _ in range(5)]
        user_id = uuid.uuid4()

        # Create one assignment per role
        assignments = [self.create_mock_assignment(role_id, user_id) for role_id in role_ids]

        # DB returns in reverse order
        mock_processor = self.create_mock_processor(list(reversed(assignments)))

        # When
        result = await load_assignments_by_role_ids(mock_processor, role_ids)

        # Then - results match input order, not DB order
        assert len(result) == 5
        for i, role_id in enumerate(role_ids):
            assert len(result[i]) == 1
            assert result[i][0].role_id == role_id

    async def test_handles_multiple_assignments_per_role(self) -> None:
        # Given
        role_id = uuid.uuid4()
        user_ids = [uuid.uuid4() for _ in range(3)]

        assignments = [self.create_mock_assignment(role_id, user_id) for user_id in user_ids]
        mock_processor = self.create_mock_processor(assignments)

        # When
        result = await load_assignments_by_role_ids(mock_processor, [role_id])

        # Then
        assert len(result) == 1
        assert len(result[0]) == 3
        assert all(a.role_id == role_id for a in result[0])
