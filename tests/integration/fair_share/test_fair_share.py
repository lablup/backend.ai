from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.fair_share import (
    BulkUpsertDomainFairShareWeightRequest,
    DomainWeightEntryInput,
    GetDomainFairShareResponse,
    GetResourceGroupFairShareSpecResponse,
    SearchDomainFairSharesRequest,
    SearchDomainFairSharesResponse,
    SearchUserFairSharesRequest,
    SearchUserFairSharesResponse,
    UpdateResourceGroupFairShareSpecRequest,
    UpdateResourceGroupFairShareSpecResponse,
    UpsertDomainFairShareWeightRequest,
    UpsertDomainFairShareWeightResponse,
)


@pytest.mark.integration
class TestFairShareWeightLifecycle:
    """Upsert domain weight → get domain fair share → search → verify weight present."""

    async def test_upsert_then_get_and_search(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        # 1. Upsert domain weight
        upsert_result = await admin_registry.fair_share.upsert_domain_fair_share_weight(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
            request=UpsertDomainFairShareWeightRequest(weight=Decimal("2.5")),
        )
        assert isinstance(upsert_result, UpsertDomainFairShareWeightResponse)
        assert upsert_result.item.domain_name == domain_fixture
        assert upsert_result.item.spec.weight == Decimal("2.5")

        # 2. Get domain fair share — should now return the record
        get_result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert isinstance(get_result, GetDomainFairShareResponse)
        assert get_result.item is not None
        assert get_result.item.domain_name == domain_fixture
        assert get_result.item.spec.weight == Decimal("2.5")

        # 3. Search domain fair shares — the record should be in results
        search_result = await admin_registry.fair_share.search_domain_fair_shares(
            SearchDomainFairSharesRequest(),
        )
        assert isinstance(search_result, SearchDomainFairSharesResponse)
        matching = [
            item
            for item in search_result.items
            if item.domain_name == domain_fixture and item.resource_group == scaling_group_fixture
        ]
        assert len(matching) >= 1
        assert matching[0].spec.weight == Decimal("2.5")


@pytest.mark.integration
class TestFairShareBulkUpsertLifecycle:
    """Bulk upsert domain weights → search → verify all present."""

    async def test_bulk_upsert_then_search(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        # 1. Bulk upsert domain weight
        bulk_result = await admin_registry.fair_share.bulk_upsert_domain_fair_share_weight(
            BulkUpsertDomainFairShareWeightRequest(
                resource_group=scaling_group_fixture,
                inputs=[
                    DomainWeightEntryInput(
                        domain_name=domain_fixture,
                        weight=Decimal("4.0"),
                    ),
                ],
            ),
        )
        assert bulk_result.upserted_count >= 1

        # 2. Search to verify
        search_result = await admin_registry.fair_share.search_domain_fair_shares(
            SearchDomainFairSharesRequest(),
        )
        matching = [
            item
            for item in search_result.items
            if item.domain_name == domain_fixture and item.resource_group == scaling_group_fixture
        ]
        assert len(matching) >= 1


@pytest.mark.integration
class TestResourceGroupSpecLifecycle:
    """Get RG spec → update spec → get again → verify updated."""

    async def test_get_update_get(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        # 1. Get original spec
        original = await admin_registry.fair_share.get_resource_group_fair_share_spec(
            resource_group=scaling_group_fixture,
        )
        assert isinstance(original, GetResourceGroupFairShareSpecResponse)
        assert original.resource_group == scaling_group_fixture

        # 2. Update spec
        update_result = await admin_registry.fair_share.update_resource_group_fair_share_spec(
            resource_group=scaling_group_fixture,
            request=UpdateResourceGroupFairShareSpecRequest(
                half_life_days=21,
                lookback_days=60,
            ),
        )
        assert isinstance(update_result, UpdateResourceGroupFairShareSpecResponse)
        assert update_result.fair_share_spec.half_life_days == 21
        assert update_result.fair_share_spec.lookback_days == 60

        # 3. Get again and verify
        updated = await admin_registry.fair_share.get_resource_group_fair_share_spec(
            resource_group=scaling_group_fixture,
        )
        assert updated.fair_share_spec.half_life_days == 21
        assert updated.fair_share_spec.lookback_days == 60


@pytest.mark.integration
class TestRGScopedFairShareAccess:
    """RG-scoped get/search for domain/project/user (auth-only access)."""

    async def test_rg_scoped_domain_get_and_search(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        # Both admin and regular user can access RG-scoped endpoints
        for registry in (admin_registry, user_registry):
            get_result = await registry.fair_share.rg_get_domain_fair_share(
                resource_group=scaling_group_fixture,
                domain_name=domain_fixture,
            )
            assert isinstance(get_result, GetDomainFairShareResponse)

            search_result = await registry.fair_share.rg_search_domain_fair_shares(
                resource_group=scaling_group_fixture,
                request=SearchDomainFairSharesRequest(),
            )
            assert isinstance(search_result, SearchDomainFairSharesResponse)

    async def test_rg_scoped_user_search(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
        group_fixture: uuid.UUID,
        admin_user_fixture: Any,
    ) -> None:
        # Both admin and regular user can access RG-scoped user search
        for registry in (admin_registry, user_registry):
            result = await registry.fair_share.rg_search_user_fair_shares(
                resource_group=scaling_group_fixture,
                domain_name=domain_fixture,
                project_id=group_fixture,
                request=SearchUserFairSharesRequest(),
            )
            assert isinstance(result, SearchUserFairSharesResponse)
            assert isinstance(result.items, list)
