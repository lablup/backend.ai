from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.fair_share import (
    BulkUpsertUserFairShareWeightRequest,
    BulkUpsertUserFairShareWeightResponse,
    GetUserFairShareResponse,
    SearchUserFairSharesRequest,
    SearchUserFairSharesResponse,
    UpsertUserFairShareWeightRequest,
    UpsertUserFairShareWeightResponse,
    UserWeightEntryInput,
)


class TestUserFairShareWeights:
    """Test user fair share weight management (global-scoped)."""

    async def test_get_user_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        admin_user_fixture: Any,
    ) -> None:
        """Get user fair share → returns weight data."""
        result = await admin_registry.fair_share.get_user_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
        )
        assert isinstance(result, GetUserFairShareResponse)
        assert result.item is not None
        assert result.item.user_uuid == admin_user_fixture.user_uuid
        assert result.item.resource_group == scaling_group_fixture

    async def test_search_user_fair_shares(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search user fair shares → paginated list."""
        result = await admin_registry.fair_share.search_user_fair_shares(
            SearchUserFairSharesRequest(),
        )
        assert isinstance(result, SearchUserFairSharesResponse)
        assert isinstance(result.items, list)

    async def test_upsert_user_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        admin_user_fixture: Any,
    ) -> None:
        """Upsert user fair share → weight created/updated."""
        weight = Decimal("4.5")
        result = await admin_registry.fair_share.upsert_user_fair_share_weight(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
            request=UpsertUserFairShareWeightRequest(
                domain_name=domain_fixture,
                weight=weight,
            ),
        )
        assert isinstance(result, UpsertUserFairShareWeightResponse)
        assert result.item.user_uuid == admin_user_fixture.user_uuid
        assert result.item.resource_group == scaling_group_fixture
        assert result.item.spec.weight == weight

        # Verify the weight persists
        get_result = await admin_registry.fair_share.get_user_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
        )
        assert get_result.item is not None
        assert get_result.item.spec.weight == weight


class TestBulkUpsertUserWeights:
    """Test bulk upsert for user weights."""

    async def test_bulk_upsert_success(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        admin_user_fixture: Any,
    ) -> None:
        """Bulk upsert success → all weights updated."""
        result = await admin_registry.fair_share.bulk_upsert_user_fair_share_weight(
            BulkUpsertUserFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[
                    UserWeightEntryInput(
                        user_uuid=admin_user_fixture.user_uuid,
                        project_id=group_fixture,
                        domain_name=domain_fixture,
                        weight=Decimal("7.0"),
                    ),
                ],
            ),
        )
        assert isinstance(result, BulkUpsertUserFairShareWeightResponse)
        assert result.upserted_count == 1

    async def test_bulk_upsert_empty_input(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Bulk upsert empty input → empty result (no error)."""
        result = await admin_registry.fair_share.bulk_upsert_user_fair_share_weight(
            BulkUpsertUserFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[],
            ),
        )
        assert isinstance(result, BulkUpsertUserFairShareWeightResponse)
        assert result.upserted_count == 0

    async def test_bulk_upsert_overwrite(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        domain_fixture: str,
        admin_user_fixture: Any,
    ) -> None:
        """Bulk upsert overwrites existing weight."""
        await admin_registry.fair_share.upsert_user_fair_share_weight(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
            request=UpsertUserFairShareWeightRequest(
                domain_name=domain_fixture,
                weight=Decimal("10.0"),
            ),
        )

        new_weight = Decimal("3.0")
        result = await admin_registry.fair_share.bulk_upsert_user_fair_share_weight(
            BulkUpsertUserFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[
                    UserWeightEntryInput(
                        user_uuid=admin_user_fixture.user_uuid,
                        project_id=group_fixture,
                        domain_name=domain_fixture,
                        weight=new_weight,
                    ),
                ],
            ),
        )
        assert isinstance(result, BulkUpsertUserFairShareWeightResponse)
        assert result.upserted_count == 1

        get_result = await admin_registry.fair_share.get_user_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
        )
        assert get_result.item is not None
        assert get_result.item.spec.weight == new_weight


class TestUserScopeAccessControl:
    """Test access control for user fair share operations."""

    async def test_global_scope_regular_user_denied(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        admin_user_fixture: Any,
    ) -> None:
        """Global-scoped user access as regular user → 403 (denied)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.get_user_fair_share(
                resource_group=scaling_group_fixture,
                project_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
            )

        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.search_user_fair_shares(
                SearchUserFairSharesRequest(),
            )

    async def test_rg_scope_regular_user_allowed(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
        group_fixture: uuid.UUID,
        admin_user_fixture: Any,
    ) -> None:
        """RG-scoped user access as regular user → 200 (allowed)."""
        get_result = await user_registry.fair_share.rg_get_user_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
        )
        assert isinstance(get_result, GetUserFairShareResponse)

        search_result = await user_registry.fair_share.rg_search_user_fair_shares(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
            project_id=group_fixture,
            request=SearchUserFairSharesRequest(),
        )
        assert isinstance(search_result, SearchUserFairSharesResponse)


class TestUserDefaultValueFallback:
    """Test default value fallback for user without fair-share record."""

    async def test_get_user_without_fair_share_default_value(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        admin_user_fixture: Any,
    ) -> None:
        """Get existing user with no fair-share row → default value returned."""
        result = await admin_registry.fair_share.get_user_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
        )
        assert isinstance(result, GetUserFairShareResponse)
        assert result.item is not None
        assert result.item.spec.weight == Decimal("1.0")
