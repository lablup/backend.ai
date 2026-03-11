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
    GetUserFairShareResponse,
    ProjectWeightEntryInput,
    SearchDomainFairSharesRequest,
    SearchDomainFairSharesResponse,
    SearchProjectFairSharesRequest,
    SearchProjectFairSharesResponse,
    SearchUserFairSharesRequest,
    SearchUserFairSharesResponse,
    UpsertDomainFairShareWeightRequest,
    UpsertDomainFairShareWeightResponse,
    UpsertProjectFairShareWeightRequest,
    UpsertProjectFairShareWeightResponse,
    UpsertUserFairShareWeightRequest,
    UpsertUserFairShareWeightResponse,
    UserWeightEntryInput,
)

# ---- Domain Fair Share Weight Management ----


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
        assert result.domain_name == domain_fixture
        assert result.resource_group == scaling_group_fixture
        assert isinstance(result.weight, Decimal)

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
        assert result.item.weight == weight

        # Verify the weight persists
        get_result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert get_result.weight == weight


# ---- Project Fair Share Weight Management ----


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
        assert result.project_id == group_fixture
        assert result.resource_group == scaling_group_fixture
        assert isinstance(result.weight, Decimal)

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
        assert result.item.weight == weight

        # Verify the weight persists
        get_result = await admin_registry.fair_share.get_project_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
        )
        assert get_result.weight == weight


# ---- User Fair Share Weight Management ----


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
        assert result.user_uuid == admin_user_fixture.user_uuid
        assert result.resource_group == scaling_group_fixture
        assert isinstance(result.weight, Decimal)

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
        assert result.item.weight == weight

        # Verify the weight persists
        get_result = await admin_registry.fair_share.get_user_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            user_uuid=admin_user_fixture.user_uuid,
        )
        assert get_result.weight == weight


# ---- Bulk Operations ----


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
        # First set a non-default weight
        await admin_registry.fair_share.upsert_domain_fair_share_weight(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
            request=UpsertDomainFairShareWeightRequest(weight=Decimal("10.0")),
        )

        # Now bulk upsert with null weight
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

        # Verify weight was reset to default (1.0)
        get_result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert get_result.weight == Decimal("1.0")


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


# ---- Scope Access Control ----


class TestScopeAccessControl:
    """Test access control for global vs RG-scoped operations."""

    async def test_global_scope_regular_user_denied(
        self,
        user_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        domain_fixture: str,
    ) -> None:
        """Global-scoped access as regular user → 403 (denied)."""
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
        """RG-scoped access as regular user → 200 (allowed)."""
        # Get
        get_result = await user_registry.fair_share.rg_get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=domain_fixture,
        )
        assert isinstance(get_result, GetDomainFairShareResponse)

        # Search
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


# ---- Default Value Fallback ----


class TestDefaultValueFallback:
    """Test default value fallback for missing records."""

    async def test_get_nonexistent_domain_default_value(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Get non-existent domain → default value returned."""
        nonexistent_domain = "nonexistent-domain-test"
        result = await admin_registry.fair_share.get_domain_fair_share(
            resource_group=scaling_group_fixture,
            domain_name=nonexistent_domain,
        )
        assert isinstance(result, GetDomainFairShareResponse)
        # Default weight should be 1.0
        assert result.weight == Decimal("1.0")

    async def test_get_nonexistent_project_default_value(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Get non-existent project → default value returned."""
        nonexistent_project = uuid.uuid4()
        result = await admin_registry.fair_share.get_project_fair_share(
            resource_group=scaling_group_fixture,
            project_id=nonexistent_project,
        )
        assert isinstance(result, GetProjectFairShareResponse)
        # Default weight should be 1.0
        assert result.weight == Decimal("1.0")

    async def test_get_nonexistent_user_default_value(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
        group_fixture: uuid.UUID,
    ) -> None:
        """Get non-existent user → default value returned."""
        nonexistent_user = uuid.uuid4()
        result = await admin_registry.fair_share.get_user_fair_share(
            resource_group=scaling_group_fixture,
            project_id=group_fixture,
            user_uuid=nonexistent_user,
        )
        assert isinstance(result, GetUserFairShareResponse)
        # Default weight should be 1.0
        assert result.weight == Decimal("1.0")
