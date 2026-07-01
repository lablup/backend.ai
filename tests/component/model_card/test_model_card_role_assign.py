"""Component tests for model card access via role assignment.

Tests the same membership gating scenarios as test_model_card_project_assign,
but membership is acquired/revoked through the RBAC role assignment SDK
(rbac.assign_role / rbac.revoke_role with project_id) instead of
project.assign_users / project.unassign_users.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    SearchModelCardsInput,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput,
    RevokeRoleInput,
)
from ai.backend.common.identifier.vfolder import VFolderUUID

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData


class TestModelCardRoleAssign:
    """Verify ASE-based membership gating when membership comes from role assignment."""

    async def test_role_member_searches_created_model_card(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        model_store_project_fixture: uuid.UUID,
        vfolder_fixture: VFolderUUID,
        role_fixture: uuid.UUID,
    ) -> None:
        """Assign role with project_id, create model card, user searches and finds it."""
        project_id = model_store_project_fixture

        # Assign role with project binding (admin SDK)
        await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(
                user_id=regular_user_fixture.user_uuid,
                role_id=role_fixture,
                project_id=project_id,
            ),
        )

        # Create model card (admin SDK — superadmin_required)
        created = await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="role-member-card",
                vfolder_id=vfolder_fixture,
                model_store_project_id=project_id,
            ),
        )

        # Regular user searches
        result = await user_v2_registry.model_card.project_search(
            project_id, SearchModelCardsInput()
        )

        assert result.total_count == 1
        assert result.items[0].id == created.model_card.id

    async def test_non_member_is_rejected(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        model_store_project_fixture: uuid.UUID,
        vfolder_fixture: VFolderUUID,
    ) -> None:
        """User without role assignment cannot search model cards."""
        project_id = model_store_project_fixture

        await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="hidden-role-card",
                vfolder_id=vfolder_fixture,
                model_store_project_id=project_id,
            ),
        )

        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.model_card.project_search(project_id, SearchModelCardsInput())

    async def test_revoked_role_loses_access(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        model_store_project_fixture: uuid.UUID,
        vfolder_fixture: VFolderUUID,
        role_fixture: uuid.UUID,
    ) -> None:
        """After role revocation, a previously accessible search fails."""
        project_id = model_store_project_fixture
        user_id = regular_user_fixture.user_uuid

        # Assign role + create card
        await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(user_id=user_id, role_id=role_fixture, project_id=project_id),
        )
        await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="ephemeral-role-card",
                vfolder_id=vfolder_fixture,
                model_store_project_id=project_id,
            ),
        )

        # Confirm search works while role is assigned
        result = await user_v2_registry.model_card.project_search(
            project_id, SearchModelCardsInput()
        )
        assert result.total_count == 1

        # Revoke role via SDK
        await admin_v2_registry.rbac.revoke_role(
            RevokeRoleInput(user_id=user_id, role_id=role_fixture),
        )

        # Search now rejected
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.model_card.project_search(project_id, SearchModelCardsInput())

    async def test_cross_project_isolation(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        model_store_project_fixture: uuid.UUID,
        second_project_fixture: uuid.UUID,
        vfolder_fixture: VFolderUUID,
        role_fixture: uuid.UUID,
    ) -> None:
        """Role assigned in project A does not grant access to project B."""
        project_a = model_store_project_fixture
        project_b = second_project_fixture
        user_id = regular_user_fixture.user_uuid

        # Assign role with project A only
        await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(user_id=user_id, role_id=role_fixture, project_id=project_a),
        )

        # Create cards in both projects
        card_a = await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="role-card-in-a",
                vfolder_id=vfolder_fixture,
                model_store_project_id=project_a,
            ),
        )
        await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="role-card-in-b",
                vfolder_id=vfolder_fixture,
                model_store_project_id=project_b,
            ),
        )

        # Project A: success
        result_a = await user_v2_registry.model_card.project_search(
            project_a, SearchModelCardsInput()
        )
        assert result_a.total_count == 1
        assert result_a.items[0].id == card_a.model_card.id

        # Project B: rejected
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.model_card.project_search(project_b, SearchModelCardsInput())
