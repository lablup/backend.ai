"""Component tests for model card access via role assignment.

Tests the same membership gating scenarios as test_model_card_project_assign,
but membership is acquired/revoked through the RBAC role assignment SDK
(rbac.assign_role / rbac.revoke_role with project_id) instead of
project.assign_users / project.unassign_users.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    SearchModelCardsInput,
)
from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput,
)

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
