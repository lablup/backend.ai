"""Component tests for project-scoped user search RBAC (project assign path).

Verifies that user.search_by_project enforces project membership via the
association_scopes_entities table (BA-5821 migration). Membership is granted
or revoked through project.assign_users / project.unassign_users SDK calls.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.group.request import (
    AssignUsersToProjectInput,
    UnassignUsersFromProjectInput,
)
from ai.backend.common.dto.manager.v2.user.request import SearchUsersRequest

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData


class TestUserSearchViaProjectAssign:
    """ASE-based project membership gating for user.search_by_project."""

    async def test_member_finds_self_in_project_search(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        target_project_fixture: uuid.UUID,
        member_role_fixture: uuid.UUID,
        admin_target_project_permission: uuid.UUID,
    ) -> None:
        """Assigned user can search project members and finds self."""
        await admin_v2_registry.project.assign_users(
            target_project_fixture,
            AssignUsersToProjectInput(
                user_ids=[regular_user_fixture.user_uuid],
                role_id=member_role_fixture,
            ),
        )

        result = await user_v2_registry.user.search_by_project(
            target_project_fixture, SearchUsersRequest()
        )

        assert result.pagination.total >= 1
        member_ids = {u.id for u in result.items}
        assert regular_user_fixture.user_uuid in member_ids

    async def test_non_member_is_rejected(
        self,
        user_v2_registry: V2ClientRegistry,
        target_project_fixture: uuid.UUID,
        member_role_fixture: uuid.UUID,
    ) -> None:
        """A user who is not a project member cannot search the project."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.user.search_by_project(
                target_project_fixture, SearchUsersRequest()
            )

    async def test_unassigned_user_loses_access(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        target_project_fixture: uuid.UUID,
        member_role_fixture: uuid.UUID,
        admin_target_project_permission: uuid.UUID,
    ) -> None:
        """After SDK unassign, project search becomes forbidden."""
        user_id = regular_user_fixture.user_uuid

        await admin_v2_registry.project.assign_users(
            target_project_fixture,
            AssignUsersToProjectInput(user_ids=[user_id], role_id=member_role_fixture),
        )
        # Sanity: search succeeds while assigned.
        await user_v2_registry.user.search_by_project(target_project_fixture, SearchUsersRequest())

        await admin_v2_registry.project.unassign_users(
            target_project_fixture,
            UnassignUsersFromProjectInput(user_ids=[user_id]),
        )

        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.user.search_by_project(
                target_project_fixture, SearchUsersRequest()
            )

    async def test_cross_project_isolation(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        target_project_fixture: uuid.UUID,
        other_project_fixture: uuid.UUID,
        member_role_fixture: uuid.UUID,
        admin_target_project_permission: uuid.UUID,
    ) -> None:
        """Membership in project A does not grant access to project B."""
        user_id = regular_user_fixture.user_uuid

        await admin_v2_registry.project.assign_users(
            target_project_fixture,
            AssignUsersToProjectInput(user_ids=[user_id], role_id=member_role_fixture),
        )

        # Project A — succeeds
        await user_v2_registry.user.search_by_project(target_project_fixture, SearchUsersRequest())

        # Project B — rejected
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.user.search_by_project(
                other_project_fixture, SearchUsersRequest()
            )
