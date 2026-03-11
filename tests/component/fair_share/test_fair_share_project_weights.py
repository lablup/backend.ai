from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.fair_share import (
    BulkUpsertProjectFairShareWeightRequest,
    BulkUpsertProjectFairShareWeightResponse,
    GetProjectFairShareResponse,
    ProjectWeightEntryInput,
    SearchProjectFairSharesRequest,
    SearchProjectFairSharesResponse,
    UpsertProjectFairShareWeightRequest,
    UpsertProjectFairShareWeightResponse,
)


class TestProjectFairShareWeights:
    """Test project fair share weight management (global-scoped)."""

    async def test_get_project_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Get project fair share → returns weight data."""
        result = await admin_registry.fair_share.get_project_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
        )
        assert isinstance(result, GetProjectFairShareResponse)
        assert result.item is not None
        assert result.item.project_id == group_fixture
        assert result.item.resource_group == scaling_group_fixture

    async def test_search_project_fair_shares(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search project fair shares → paginated list."""
        result = await admin_registry.fair_share.search_project_fair_shares(
            SearchProjectFairSharesRequest(),
        )
        assert isinstance(result, SearchProjectFairSharesResponse)
        assert isinstance(result.items, list)

    async def test_upsert_project_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        domain_fixture: str,
    ) -> None:
        """Upsert project fair share → weight created/updated."""
        weight = Decimal("3.5")
        result = await admin_registry.fair_share.upsert_project_fair_share_weight(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            request=UpsertProjectFairShareWeightRequest(
                domain_name=domain_fixture,
                weight=weight,
            ),
        )
        assert isinstance(result, UpsertProjectFairShareWeightResponse)
        assert result.item.project_id == group_fixture
        assert result.item.resource_group == scaling_group_fixture
        assert result.item.spec.weight == weight

        # Verify the weight persists
        get_result = await admin_registry.fair_share.get_project_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
        )
        assert get_result.item is not None
        assert get_result.item.spec.weight == weight


class TestBulkUpsertProjectWeights:
    """Test bulk upsert for project weights."""

    async def test_bulk_upsert_success(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        domain_fixture: str,
    ) -> None:
        """Bulk upsert success → all weights updated."""
        result = await admin_registry.fair_share.bulk_upsert_project_fair_share_weight(
            BulkUpsertProjectFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[
                    ProjectWeightEntryInput(
                        project_id=group_fixture,
                        domain_name=domain_fixture,
                        weight=Decimal("6.0"),
                    ),
                ],
            ),
        )
        assert isinstance(result, BulkUpsertProjectFairShareWeightResponse)
        assert result.upserted_count == 1

    async def test_bulk_upsert_empty_input(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Bulk upsert empty input → empty result (no error)."""
        result = await admin_registry.fair_share.bulk_upsert_project_fair_share_weight(
            BulkUpsertProjectFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[],
            ),
        )
        assert isinstance(result, BulkUpsertProjectFairShareWeightResponse)
        assert result.upserted_count == 0

    async def test_bulk_upsert_null_weight(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
        domain_fixture: str,
    ) -> None:
        """Bulk upsert with null weight → weight reset to default."""
        await admin_registry.fair_share.upsert_project_fair_share_weight(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            request=UpsertProjectFairShareWeightRequest(
                domain_name=domain_fixture,
                weight=Decimal("10.0"),
            ),
        )

        result = await admin_registry.fair_share.bulk_upsert_project_fair_share_weight(
            BulkUpsertProjectFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[
                    ProjectWeightEntryInput(
                        project_id=group_fixture,
                        domain_name=domain_fixture,
                        weight=None,
                    ),
                ],
            ),
        )
        assert isinstance(result, BulkUpsertProjectFairShareWeightResponse)
        assert result.upserted_count == 1

        get_result = await admin_registry.fair_share.get_project_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
        )
        assert get_result.item is not None
        assert get_result.item.spec.weight == Decimal("1.0")


class TestProjectScopeAccessControl:
    """Test access control for project fair share operations."""

    async def test_global_scope_regular_user_denied(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Global-scoped project access as regular user → 403 (denied)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.get_project_fair_share(
                resource_group=scaling_group_fixture,
                project_id=group_fixture,
            )

        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.search_project_fair_shares(
                SearchProjectFairSharesRequest(),
            )

    async def test_rg_scope_regular_user_allowed(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """RG-scoped project access as regular user → 200 (allowed)."""
        get_result = await user_registry.fair_share.rg_get_project_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
            project_id=group_fixture,
        )
        assert isinstance(get_result, GetProjectFairShareResponse)

        search_result = await user_registry.fair_share.rg_search_project_fair_shares(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
            request=SearchProjectFairSharesRequest(),
        )
        assert isinstance(search_result, SearchProjectFairSharesResponse)


class TestProjectDefaultValueFallback:
    """Test default value fallback for project without fair-share record."""

    async def test_get_project_without_fair_share_default_value(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Get existing project with no fair-share row → default value returned."""
        result = await admin_registry.fair_share.get_project_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
        )
        assert isinstance(result, GetProjectFairShareResponse)
        assert result.item is not None
        assert result.item.spec.weight == Decimal("1.0")
