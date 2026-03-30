"""Component tests for admin keypair v2 CRUD.

Test matrix:
  - Admin search: returns results
  - Admin create: create keypair for a user
  - Admin get: get keypair by access_key
  - Admin update: toggle is_active
  - Admin delete: delete keypair
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.keypair.request import (
    AdminCreateKeypairInput,
    AdminSearchKeypairsInput,
    AdminUpdateKeypairInput,
    KeypairFilter,
)

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData


class TestAdminKeypairSearch:
    """Tests for admin keypair search via POST /v2/keypairs/search."""

    async def test_admin_search_returns_items(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """Admin search should return keypairs."""
        result = await admin_v2_registry.keypair.admin_search(
            AdminSearchKeypairsInput(limit=10, offset=0)
        )
        assert result.pagination.total >= 0
        assert isinstance(result.items, list)


class TestAdminKeypairCRUD:
    """Tests for admin keypair create/get/update/delete."""

    async def test_admin_create_and_get(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        """Admin creates a keypair and retrieves it."""
        create_result = await admin_v2_registry.keypair.admin_create(
            AdminCreateKeypairInput(
                user_id=admin_user_fixture.user_uuid,
                resource_policy="default",
                is_active=True,
                is_admin=False,
                rate_limit=10000,
            )
        )
        assert create_result.keypair.access_key
        assert create_result.secret_key
        assert create_result.keypair.rate_limit == 10000
        assert create_result.keypair.is_active is True

        # Get the created keypair
        access_key = create_result.keypair.access_key
        get_result = await admin_v2_registry.keypair.admin_get(access_key)
        assert get_result.access_key == access_key
        assert get_result.rate_limit == 10000

        # Cleanup
        await admin_v2_registry.keypair.admin_delete(access_key)

    async def test_admin_update_keypair(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        """Admin creates a keypair, then updates it."""
        create_result = await admin_v2_registry.keypair.admin_create(
            AdminCreateKeypairInput(
                user_id=admin_user_fixture.user_uuid,
                resource_policy="default",
                is_active=True,
                is_admin=False,
                rate_limit=10000,
            )
        )
        access_key = create_result.keypair.access_key

        # Update the keypair
        update_result = await admin_v2_registry.keypair.admin_update(
            AdminUpdateKeypairInput(
                access_key=access_key,
                is_active=False,
                rate_limit=5000,
            )
        )
        assert update_result.keypair.is_active is False
        assert update_result.keypair.rate_limit == 5000

        # Cleanup
        await admin_v2_registry.keypair.admin_delete(access_key)

    async def test_admin_delete_keypair(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        """Admin creates and deletes a keypair."""
        create_result = await admin_v2_registry.keypair.admin_create(
            AdminCreateKeypairInput(
                user_id=admin_user_fixture.user_uuid,
                resource_policy="default",
                is_active=True,
                is_admin=False,
                rate_limit=10000,
            )
        )
        access_key = create_result.keypair.access_key

        delete_result = await admin_v2_registry.keypair.admin_delete(access_key)
        assert delete_result.access_key == access_key

    async def test_admin_search_with_filter(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        """Admin search with is_active filter."""
        # Create a keypair for filtering
        create_result = await admin_v2_registry.keypair.admin_create(
            AdminCreateKeypairInput(
                user_id=admin_user_fixture.user_uuid,
                resource_policy="default",
                is_active=True,
                is_admin=False,
            )
        )
        access_key = create_result.keypair.access_key

        result = await admin_v2_registry.keypair.admin_search(
            AdminSearchKeypairsInput(
                filter=KeypairFilter(is_active=True),
                limit=100,
                offset=0,
            )
        )
        assert result.pagination.total >= 1
        active_keys = [item.access_key for item in result.items]
        assert access_key in active_keys

        # Cleanup
        await admin_v2_registry.keypair.admin_delete(access_key)
