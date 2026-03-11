from __future__ import annotations

from decimal import Decimal

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.fair_share import (
    BulkUpsertDomainFairShareWeightRequest,
    BulkUpsertDomainFairShareWeightResponse,
    DomainWeightEntryInput,
    GetDomainFairShareResponse,
    SearchDomainFairSharesRequest,
    SearchDomainFairSharesResponse,
    UpsertDomainFairShareWeightRequest,
    UpsertDomainFairShareWeightResponse,
)


class TestDomainFairShareWeights:
    """Test domain fair share weight management (global-scoped)."""

    async def test_get_domain_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        """Get domain fair share → returns weight data."""
        result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert isinstance(result, GetDomainFairShareResponse)
        assert result.item is not None
        assert result.item.domain_name == domain_fixture
        assert result.item.resource_group == scaling_group_fixture

    async def test_search_domain_fair_shares(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search domain fair shares → paginated list."""
        result = await admin_registry.fair_share.search_domain_fair_shares(
            SearchDomainFairSharesRequest(),
        )
        assert isinstance(result, SearchDomainFairSharesResponse)
        assert isinstance(result.items, list)

    async def test_upsert_domain_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        """Upsert domain fair share → weight created/updated."""
        weight = Decimal("2.5")
        result = await admin_registry.fair_share.upsert_domain_fair_share_weight(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
            request=UpsertDomainFairShareWeightRequest(weight=weight),
        )
        assert isinstance(result, UpsertDomainFairShareWeightResponse)
        assert result.item.domain_name == domain_fixture
        assert result.item.resource_group == scaling_group_fixture
        assert result.item.spec.weight == weight

        # Verify the weight persists
        get_result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert get_result.item is not None
        assert get_result.item.spec.weight == weight


class TestBulkUpsertDomainWeights:
    """Test bulk upsert for domain weights."""

    async def test_bulk_upsert_success(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        """Bulk upsert success → all weights updated."""
        result = await admin_registry.fair_share.bulk_upsert_domain_fair_share_weight(
            BulkUpsertDomainFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[
                    DomainWeightEntryInput(
                        domain_name=domain_fixture,
                        weight=Decimal("5.0"),
                    ),
                ],
            ),
        )
        assert isinstance(result, BulkUpsertDomainFairShareWeightResponse)
        assert result.upserted_count == 1

    async def test_bulk_upsert_empty_input(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Bulk upsert empty input → empty result (no error)."""
        result = await admin_registry.fair_share.bulk_upsert_domain_fair_share_weight(
            BulkUpsertDomainFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[],
            ),
        )
        assert isinstance(result, BulkUpsertDomainFairShareWeightResponse)
        assert result.upserted_count == 0

    async def test_bulk_upsert_null_weight(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        """Bulk upsert with null weight → weight reset to default."""
        await admin_registry.fair_share.upsert_domain_fair_share_weight(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
            request=UpsertDomainFairShareWeightRequest(weight=Decimal("10.0")),
        )

        result = await admin_registry.fair_share.bulk_upsert_domain_fair_share_weight(
            BulkUpsertDomainFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[
                    DomainWeightEntryInput(
                        domain_name=domain_fixture,
                        weight=None,
                    ),
                ],
            ),
        )
        assert isinstance(result, BulkUpsertDomainFairShareWeightResponse)
        assert result.upserted_count == 1

        get_result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert get_result.item is not None
        assert get_result.item.spec.weight == Decimal("1.0")


class TestDomainScopeAccessControl:
    """Test access control for domain fair share operations."""

    async def test_global_scope_regular_user_denied(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        """Global-scoped domain access as regular user → 403 (denied)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.get_domain_fair_share(
                resource_group=scaling_group_fixture,
                domain_name=domain_fixture,
            )

        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.search_domain_fair_shares(
                SearchDomainFairSharesRequest(),
            )

        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.upsert_domain_fair_share_weight(
                resource_group=scaling_group_fixture,
                domain_name=domain_fixture,
                request=UpsertDomainFairShareWeightRequest(weight=Decimal("1.0")),
            )

    async def test_rg_scope_regular_user_allowed(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        """RG-scoped domain access as regular user → 200 (allowed)."""
        get_result = await user_registry.fair_share.rg_get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert isinstance(get_result, GetDomainFairShareResponse)

        search_result = await user_registry.fair_share.rg_search_domain_fair_shares(
            resource_group=scaling_group_fixture,
            request=SearchDomainFairSharesRequest(),
        )
        assert isinstance(search_result, SearchDomainFairSharesResponse)

    async def test_global_scope_admin_allowed(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        """Admin global scope access → 200 (allowed)."""
        result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert isinstance(result, GetDomainFairShareResponse)


class TestDomainDefaultValueFallback:
    """Test default value fallback for domain without fair-share record."""

    async def test_get_domain_without_fair_share_default_value(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        """Get existing domain with no fair-share row → default value returned."""
        result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert isinstance(result, GetDomainFairShareResponse)
        assert result.item is not None
        assert result.item.spec.weight == Decimal("1.0")
