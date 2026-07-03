from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.fair_share import (
    BulkUpsertDomainFairShareWeightRequest,
    BulkUpsertDomainFairShareWeightResponse,
    BulkUpsertProjectFairShareWeightRequest,
    BulkUpsertProjectFairShareWeightResponse,
    BulkUpsertUserFairShareWeightRequest,
    BulkUpsertUserFairShareWeightResponse,
    DomainWeightEntryInput,
    GetDomainFairShareResponse,
    GetProjectFairShareResponse,
    GetResourceGroupFairShareSpecResponse,
    GetUserFairShareResponse,
    ProjectWeightEntryInput,
    SearchDomainFairSharesRequest,
    SearchDomainFairSharesResponse,
    SearchDomainUsageBucketsRequest,
    SearchDomainUsageBucketsResponse,
    SearchProjectFairSharesRequest,
    SearchProjectFairSharesResponse,
    SearchProjectUsageBucketsRequest,
    SearchProjectUsageBucketsResponse,
    SearchResourceGroupFairShareSpecsResponse,
    SearchUserFairSharesRequest,
    SearchUserFairSharesResponse,
    SearchUserUsageBucketsRequest,
    SearchUserUsageBucketsResponse,
    UpdateResourceGroupFairShareSpecRequest,
    UpdateResourceGroupFairShareSpecResponse,
    UpsertDomainFairShareWeightRequest,
    UpsertDomainFairShareWeightResponse,
    UpsertProjectFairShareWeightRequest,
    UpsertProjectFairShareWeightResponse,
    UpsertUserFairShareWeightRequest,
    UpsertUserFairShareWeightResponse,
    UserWeightEntryInput,
)
from ai.backend.testutils.fixtures import DomainFixtureData, ScalingGroupFixtureData

# ---- Domain Fair Share (Global-scoped) ----


class TestGetDomainFairShare:
    async def test_admin_get_domain_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
        )
        assert isinstance(result, GetDomainFairShareResponse)

    async def test_user_get_domain_fair_share_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.get_domain_fair_share(
                resource_group=scaling_group_fixture.scaling_group_name,
                domain_name=domain_fixture.domain_name,
            )


class TestSearchDomainFairShares:
    async def test_admin_search_domain_fair_shares(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.fair_share.search_domain_fair_shares(
            SearchDomainFairSharesRequest(),
        )
        assert isinstance(result, SearchDomainFairSharesResponse)
        assert isinstance(result.items, list)

    async def test_user_search_domain_fair_shares_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.search_domain_fair_shares(
                SearchDomainFairSharesRequest(),
            )


# ---- Project Fair Share (Global-scoped) ----


class TestGetProjectFairShare:
    async def test_admin_get_project_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        group_fixture: uuid.UUID,
    ) -> None:
        result = await admin_registry.fair_share.get_project_fair_share(
            resource_group=scaling_group_fixture.scaling_group_name,
            project_id=group_fixture,
        )
        assert isinstance(result, GetProjectFairShareResponse)

    async def test_user_get_project_fair_share_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        group_fixture: uuid.UUID,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.get_project_fair_share(
                resource_group=scaling_group_fixture.scaling_group_name,
                project_id=group_fixture,
            )


class TestSearchProjectFairShares:
    async def test_admin_search_project_fair_shares(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.fair_share.search_project_fair_shares(
            SearchProjectFairSharesRequest(),
        )
        assert isinstance(result, SearchProjectFairSharesResponse)
        assert isinstance(result.items, list)


# ---- User Fair Share (Global-scoped) ----


class TestGetUserFairShare:
    async def test_admin_get_user_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        group_fixture: uuid.UUID,
        admin_user_fixture: Any,
    ) -> None:
        result = await admin_registry.fair_share.get_user_fair_share(
            resource_group=scaling_group_fixture.scaling_group_name,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
        )
        assert isinstance(result, GetUserFairShareResponse)

    async def test_user_get_user_fair_share_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        group_fixture: uuid.UUID,
        regular_user_fixture: Any,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.get_user_fair_share(
                resource_group=scaling_group_fixture.scaling_group_name,
                project_id=group_fixture,
                user_uuid=regular_user_fixture.user_uuid,
            )


class TestSearchUserFairShares:
    async def test_admin_search_user_fair_shares(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.fair_share.search_user_fair_shares(
            SearchUserFairSharesRequest(),
        )
        assert isinstance(result, SearchUserFairSharesResponse)
        assert isinstance(result.items, list)


# ---- Usage Buckets (Global-scoped) ----


class TestSearchDomainUsageBuckets:
    async def test_admin_search_domain_usage_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.fair_share.search_domain_usage_buckets(
            SearchDomainUsageBucketsRequest(),
        )
        assert isinstance(result, SearchDomainUsageBucketsResponse)
        assert isinstance(result.items, list)


class TestSearchProjectUsageBuckets:
    async def test_admin_search_project_usage_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.fair_share.search_project_usage_buckets(
            SearchProjectUsageBucketsRequest(),
        )
        assert isinstance(result, SearchProjectUsageBucketsResponse)
        assert isinstance(result.items, list)


class TestSearchUserUsageBuckets:
    async def test_admin_search_user_usage_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.fair_share.search_user_usage_buckets(
            SearchUserUsageBucketsRequest(),
        )
        assert isinstance(result, SearchUserUsageBucketsResponse)
        assert isinstance(result.items, list)


# ---- RG-Scoped Domain Fair Share ----


class TestRGGetDomainFairShare:
    async def test_admin_rg_get_domain_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.rg_get_domain_fair_share(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
        )
        assert isinstance(result, GetDomainFairShareResponse)

    async def test_user_rg_get_domain_fair_share(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await user_registry.fair_share.rg_get_domain_fair_share(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
        )
        assert isinstance(result, GetDomainFairShareResponse)


class TestRGSearchDomainFairShares:
    async def test_admin_rg_search_domain_fair_shares(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.rg_search_domain_fair_shares(
            resource_group=scaling_group_fixture.scaling_group_name,
            request=SearchDomainFairSharesRequest(),
        )
        assert isinstance(result, SearchDomainFairSharesResponse)
        assert isinstance(result.items, list)


# ---- RG-Scoped Project Fair Share ----


class TestRGGetProjectFairShare:
    async def test_admin_rg_get_project_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
        group_fixture: uuid.UUID,
    ) -> None:
        result = await admin_registry.fair_share.rg_get_project_fair_share(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
            project_id=group_fixture,
        )
        assert isinstance(result, GetProjectFairShareResponse)


class TestRGSearchProjectFairShares:
    async def test_admin_rg_search_project_fair_shares(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.rg_search_project_fair_shares(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
            request=SearchProjectFairSharesRequest(),
        )
        assert isinstance(result, SearchProjectFairSharesResponse)
        assert isinstance(result.items, list)


# ---- RG-Scoped User Fair Share ----


class TestRGGetUserFairShare:
    async def test_admin_rg_get_user_fair_share(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
        group_fixture: uuid.UUID,
        admin_user_fixture: Any,
    ) -> None:
        result = await admin_registry.fair_share.rg_get_user_fair_share(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
        )
        assert isinstance(result, GetUserFairShareResponse)


class TestRGSearchUserFairShares:
    async def test_admin_rg_search_user_fair_shares(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
        group_fixture: uuid.UUID,
    ) -> None:
        result = await admin_registry.fair_share.rg_search_user_fair_shares(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
            project_id=group_fixture,
            request=SearchUserFairSharesRequest(),
        )
        assert isinstance(result, SearchUserFairSharesResponse)
        assert isinstance(result.items, list)


# ---- RG-Scoped Usage Buckets ----


class TestRGSearchDomainUsageBuckets:
    async def test_admin_rg_search_domain_usage_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.rg_search_domain_usage_buckets(
            resource_group=scaling_group_fixture.scaling_group_name,
            request=SearchDomainUsageBucketsRequest(),
        )
        assert isinstance(result, SearchDomainUsageBucketsResponse)
        assert isinstance(result.items, list)


class TestRGSearchProjectUsageBuckets:
    async def test_admin_rg_search_project_usage_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.rg_search_project_usage_buckets(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
            request=SearchProjectUsageBucketsRequest(),
        )
        assert isinstance(result, SearchProjectUsageBucketsResponse)
        assert isinstance(result.items, list)


class TestRGSearchUserUsageBuckets:
    async def test_admin_rg_search_user_usage_buckets(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
        group_fixture: uuid.UUID,
    ) -> None:
        result = await admin_registry.fair_share.rg_search_user_usage_buckets(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
            project_id=group_fixture,
            request=SearchUserUsageBucketsRequest(),
        )
        assert isinstance(result, SearchUserUsageBucketsResponse)
        assert isinstance(result.items, list)


# ---- Upsert Weights (Global-scoped) ----


class TestUpsertDomainFairShareWeight:
    async def test_admin_upsert_domain_weight(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.upsert_domain_fair_share_weight(
            resource_group=scaling_group_fixture.scaling_group_name,
            domain_name=domain_fixture.domain_name,
            request=UpsertDomainFairShareWeightRequest(weight=Decimal("1.5")),
        )
        assert isinstance(result, UpsertDomainFairShareWeightResponse)
        assert result.item.domain_name == domain_fixture.domain_name
        assert result.item.resource_group == scaling_group_fixture.scaling_group_name

    async def test_user_upsert_domain_weight_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.upsert_domain_fair_share_weight(
                resource_group=scaling_group_fixture.scaling_group_name,
                domain_name=domain_fixture.domain_name,
                request=UpsertDomainFairShareWeightRequest(weight=Decimal("1.0")),
            )


class TestUpsertProjectFairShareWeight:
    async def test_admin_upsert_project_weight(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.upsert_project_fair_share_weight(
            resource_group=scaling_group_fixture.scaling_group_name,
            project_id=group_fixture,
            request=UpsertProjectFairShareWeightRequest(
                domain_name=domain_fixture.domain_name,
                weight=Decimal("2.0"),
            ),
        )
        assert isinstance(result, UpsertProjectFairShareWeightResponse)
        assert result.item.project_id == group_fixture
        assert result.item.resource_group == scaling_group_fixture.scaling_group_name


class TestUpsertUserFairShareWeight:
    async def test_admin_upsert_user_weight(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        admin_user_fixture: Any,
    ) -> None:
        result = await admin_registry.fair_share.upsert_user_fair_share_weight(
            resource_group=scaling_group_fixture.scaling_group_name,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
            request=UpsertUserFairShareWeightRequest(
                domain_name=domain_fixture.domain_name,
                weight=Decimal("3.0"),
            ),
        )
        assert isinstance(result, UpsertUserFairShareWeightResponse)
        assert result.item.user_uuid == admin_user_fixture.user_uuid
        assert result.item.resource_group == scaling_group_fixture.scaling_group_name


# ---- Bulk Upsert Weights (Global-scoped) ----


class TestBulkUpsertDomainFairShareWeight:
    async def test_admin_bulk_upsert_domain_weight(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.bulk_upsert_domain_fair_share_weight(
            BulkUpsertDomainFairShareWeightRequest(
                resource_group=scaling_group_fixture.scaling_group_name,
                inputs=[
                    DomainWeightEntryInput(
                        domain_name=domain_fixture.domain_name,
                        weight=Decimal("1.0"),
                    ),
                ],
            ),
        )
        assert isinstance(result, BulkUpsertDomainFairShareWeightResponse)
        assert result.upserted_count >= 1


class TestBulkUpsertProjectFairShareWeight:
    async def test_admin_bulk_upsert_project_weight(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.bulk_upsert_project_fair_share_weight(
            BulkUpsertProjectFairShareWeightRequest(
                resource_group=scaling_group_fixture.scaling_group_name,
                inputs=[
                    ProjectWeightEntryInput(
                        project_id=group_fixture,
                        domain_name=domain_fixture.domain_name,
                        weight=Decimal("2.0"),
                    ),
                ],
            ),
        )
        assert isinstance(result, BulkUpsertProjectFairShareWeightResponse)
        assert result.upserted_count >= 1


class TestBulkUpsertUserFairShareWeight:
    async def test_admin_bulk_upsert_user_weight(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        admin_user_fixture: Any,
    ) -> None:
        result = await admin_registry.fair_share.bulk_upsert_user_fair_share_weight(
            BulkUpsertUserFairShareWeightRequest(
                resource_group=scaling_group_fixture.scaling_group_name,
                inputs=[
                    UserWeightEntryInput(
                        user_uuid=admin_user_fixture.user_uuid,
                        project_id=group_fixture,
                        domain_name=domain_fixture.domain_name,
                        weight=Decimal("3.0"),
                    ),
                ],
            ),
        )
        assert isinstance(result, BulkUpsertUserFairShareWeightResponse)
        assert result.upserted_count >= 1


# ---- Resource Group Fair Share Spec (Global-scoped) ----


class TestGetResourceGroupFairShareSpec:
    async def test_admin_get_rg_spec(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.get_resource_group_fair_share_spec(
            resource_group=scaling_group_fixture.scaling_group_name,
        )
        assert isinstance(result, GetResourceGroupFairShareSpecResponse)
        assert result.resource_group == scaling_group_fixture.scaling_group_name

    async def test_user_get_rg_spec_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.fair_share.get_resource_group_fair_share_spec(
                resource_group=scaling_group_fixture.scaling_group_name,
            )


class TestSearchResourceGroupFairShareSpecs:
    async def test_admin_search_rg_specs(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.fair_share.search_resource_group_fair_share_specs()
        assert isinstance(result, SearchResourceGroupFairShareSpecsResponse)
        assert isinstance(result.items, list)


class TestUpdateResourceGroupFairShareSpec:
    async def test_admin_update_rg_spec(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
    ) -> None:
        result = await admin_registry.fair_share.update_resource_group_fair_share_spec(
            resource_group=scaling_group_fixture.scaling_group_name,
            request=UpdateResourceGroupFairShareSpecRequest(
                half_life_days=14,
            ),
        )
        assert isinstance(result, UpdateResourceGroupFairShareSpecResponse)
        assert result.resource_group == scaling_group_fixture.scaling_group_name
        assert result.fair_share_spec.half_life_days == 14

    async def test_admin_partial_update_preserves_other_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: ScalingGroupFixtureData,
    ) -> None:
        """Partial update (merge logic) changes only the specified field."""
        current = await admin_registry.fair_share.get_resource_group_fair_share_spec(
            resource_group=scaling_group_fixture.scaling_group_name,
        )
        original_half_life = current.fair_share_spec.half_life_days
        original_lookback = current.fair_share_spec.lookback_days

        new_half_life = original_half_life + 1
        result = await admin_registry.fair_share.update_resource_group_fair_share_spec(
            resource_group=scaling_group_fixture.scaling_group_name,
            request=UpdateResourceGroupFairShareSpecRequest(
                half_life_days=new_half_life,
            ),
        )

        assert result.fair_share_spec.half_life_days == new_half_life
        assert result.fair_share_spec.lookback_days == original_lookback

        # Restore
        await admin_registry.fair_share.update_resource_group_fair_share_spec(
            resource_group=scaling_group_fixture.scaling_group_name,
            request=UpdateResourceGroupFairShareSpecRequest(
                half_life_days=original_half_life,
            ),
        )
