"""Component tests for project-scoped user search RBAC (role assign path).

Verifies that user.search_by_project enforces project membership when
membership is granted via the RBAC role assignment SDK
(rbac.assign_role / rbac.revoke_role with project_id).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput,
    RevokeRoleInput,
)
from ai.backend.common.dto.manager.v2.user.request import SearchUsersRequest

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData


class TestUserSearchViaRoleAssign:
    """ASE-based project membership gating via role assignment SDK."""

    async def test_role_member_finds_self_in_project_search(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        target_project_fixture: uuid.UUID,
        member_role_fixture: uuid.UUID,
    ) -> None:
        """User with role assigned in the project can search and finds self."""
        await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(
                user_id=regular_user_fixture.user_uuid,
                role_id=member_role_fixture,
                project_id=target_project_fixture,
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
        """A user without role assignment cannot search the project."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.user.search_by_project(
                target_project_fixture, SearchUsersRequest()
            )

    async def test_revoked_role_loses_access(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        target_project_fixture: uuid.UUID,
        member_role_fixture: uuid.UUID,
    ) -> None:
        """After role revocation, project search becomes forbidden."""
        user_id = regular_user_fixture.user_uuid

        await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(
                user_id=user_id,
                role_id=member_role_fixture,
                project_id=target_project_fixture,
            ),
        )
        # Sanity: search succeeds while role is assigned.
        await user_v2_registry.user.search_by_project(target_project_fixture, SearchUsersRequest())

        await admin_v2_registry.rbac.revoke_role(
            RevokeRoleInput(user_id=user_id, role_id=member_role_fixture),
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
    ) -> None:
        """Role assigned in project A does not grant access to project B."""
        user_id = regular_user_fixture.user_uuid

        await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(
                user_id=user_id,
                role_id=member_role_fixture,
                project_id=target_project_fixture,
            ),
        )

        # Project A — succeeds
        await user_v2_registry.user.search_by_project(target_project_fixture, SearchUsersRequest())

        # Project B — rejected
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.user.search_by_project(
                other_project_fixture, SearchUsersRequest()
            )
