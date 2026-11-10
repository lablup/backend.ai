"""Component tests for model card project-scoped RBAC.

All mutations (assign, unassign, create model card) go through the SDK;
only DB-level fixtures are used for entities that require a storage proxy
(vfolders) or that have no v2 SDK yet (MODEL_STORE project type).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.dto.manager.v2.group.request import (
    AssignUsersToProjectInput,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    SearchModelCardsInput,
)

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData


class TestModelCardRBAC:
    """Verify ASE-based project membership gating for model card operations."""

    async def test_member_searches_created_model_card(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        model_store_project_fixture: uuid.UUID,
        vfolder_fixture: VFolderUUID,
        role_fixture: uuid.UUID,
    ) -> None:
        """Assign user via SDK, create model card via SDK, user searches and finds it."""
        project_id = model_store_project_fixture

        # Assign regular user to project (admin SDK)
        await admin_v2_registry.project.assign_users(
            project_id,
            AssignUsersToProjectInput(
                user_ids=[regular_user_fixture.user_uuid],
                role_id=role_fixture,
            ),
        )

        # Create model card in the project (admin SDK — superadmin_required)
        created = await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="member-card",
                vfolder_id=vfolder_fixture,
                model_store_project_id=project_id,
            ),
        )

        # Regular user searches in project scope
        result = await user_v2_registry.model_card.project_search(
            project_id, SearchModelCardsInput()
        )

        assert result.total_count == 1
        assert result.items[0].id == created.model_card.id
