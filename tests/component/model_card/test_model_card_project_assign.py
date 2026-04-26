"""Component tests for model card project-scoped RBAC.

All mutations (assign, unassign, create model card) go through the SDK;
only DB-level fixtures are used for entities that require a storage proxy
(vfolders) or that have no v2 SDK yet (MODEL_STORE project type).
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
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    SearchModelCardsInput,
)
from ai.backend.common.identifier.vfolder import VFolderUUID

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

    async def test_non_member_is_rejected(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        model_store_project_fixture: uuid.UUID,
        vfolder_fixture: VFolderUUID,
    ) -> None:
        """Non-member user cannot search model cards in the project."""
        project_id = model_store_project_fixture

        # Create model card (admin SDK) — user is NOT assigned
        await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="hidden-card",
                vfolder_id=vfolder_fixture,
                model_store_project_id=project_id,
            ),
        )

        # Regular user search → 403
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.model_card.project_search(project_id, SearchModelCardsInput())

    async def test_unassigned_user_loses_access(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        regular_user_fixture: UserFixtureData,
        model_store_project_fixture: uuid.UUID,
        vfolder_fixture: VFolderUUID,
        role_fixture: uuid.UUID,
    ) -> None:
        """After SDK unassign, a previously accessible search fails."""
        project_id = model_store_project_fixture
        user_id = regular_user_fixture.user_uuid

        # Assign + create card
        await admin_v2_registry.project.assign_users(
            project_id,
            AssignUsersToProjectInput(user_ids=[user_id], role_id=role_fixture),
        )
        await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="ephemeral-card",
                vfolder_id=vfolder_fixture,
                model_store_project_id=project_id,
            ),
        )

        # Confirm search works while assigned
        result = await user_v2_registry.model_card.project_search(
            project_id, SearchModelCardsInput()
        )
        assert result.total_count == 1

        # Unassign via SDK
        await admin_v2_registry.project.unassign_users(
            project_id,
            UnassignUsersFromProjectInput(user_ids=[user_id]),
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
        """Membership in project A does not grant access to project B."""
        project_a = model_store_project_fixture
        project_b = second_project_fixture
        user_id = regular_user_fixture.user_uuid

        # Assign user to project A only
        await admin_v2_registry.project.assign_users(
            project_a,
            AssignUsersToProjectInput(user_ids=[user_id], role_id=role_fixture),
        )

        # Create cards in both projects
        card_a = await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="card-in-a",
                vfolder_id=vfolder_fixture,
                model_store_project_id=project_a,
            ),
        )
        await admin_v2_registry.model_card.create(
            CreateModelCardInput(
                name="card-in-b",
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
