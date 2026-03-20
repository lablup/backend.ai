"""Tests for Domain Fair Share GQL query resolvers."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from aiohttp import web

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.v2.fair_share.response import (
    GetDomainFairSharePayload,
    SearchDomainFairSharesPayload,
)
from ai.backend.common.types import ResourceSlot, SlotQuantity
from ai.backend.manager.api.adapters.fair_share import FairShareAdapter
from ai.backend.manager.api.gql.fair_share.resolver import domain as domain_resolver
from ai.backend.manager.api.gql.fair_share.types.domain import (
    DomainFairShareConnection,
    DomainFairShareGQL,
)
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    FairShareCalculationSnapshot,
    FairShareData,
    FairShareMetadata,
    FairShareSpec,
)
from ai.backend.manager.errors.resource import DomainNotFound

# Common fixtures


@pytest.fixture
def mock_superadmin_user() -> UserData:
    """Create mock superadmin user."""
    return UserData(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        is_authorized=True,
        is_admin=True,
        is_superadmin=True,
        role=UserRole.SUPERADMIN,
        domain_name="default",
    )


@pytest.fixture
def mock_regular_user() -> UserData:
    """Create mock regular (non-superadmin) user."""
    return UserData(
        user_id=UUID("00000000-0000-0000-0000-000000000002"),
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="default",
    )


@pytest.fixture
def sample_domain_fair_share_data() -> DomainFairShareData:
    """Create sample DomainFairShareData."""
    now = datetime.now(UTC)
    today = now.date()
    return DomainFairShareData(
        resource_group="default",
        domain_name="test-domain",
        data=FairShareData(
            spec=FairShareSpec(
                weight=Decimal("2.0"),
                half_life_days=14,
                lookback_days=30,
                decay_unit_days=1,
                resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
            ),
            calculation_snapshot=FairShareCalculationSnapshot(
                fair_share_factor=Decimal("1.5"),
                total_decayed_usage=[
                    SlotQuantity("cpu", Decimal("100.0")),
                    SlotQuantity("mem", Decimal("200.0")),
                ],
                normalized_usage=Decimal("50.0"),
                lookback_start=today,
                lookback_end=today,
                last_calculated_at=now,
            ),
            metadata=FairShareMetadata(
                created_at=now,
                updated_at=now,
            ),
            use_default=False,
        ),
    )


def create_mock_info(context: MagicMock) -> MagicMock:
    """Create mock strawberry.Info with context."""
    info = MagicMock()
    info.context = context
    return info


# Admin Single Query Tests


class TestAdminDomainFairShareSingleQuery:
    async def test_admin_domain_fair_share_calls_adapter_with_correct_input(
        self,
        mock_superadmin_user: UserData,
        sample_domain_fair_share_data: DomainFairShareData,
    ) -> None:
        """Should call adapter with correct GetDomainFairShareInput."""
        domain_node = FairShareAdapter._domain_data_to_dto(sample_domain_fair_share_data)
        context = MagicMock()
        context.adapters.fair_share.get_domain = AsyncMock(
            return_value=GetDomainFairSharePayload(item=domain_node)
        )
        info = create_mock_info(context)

        with with_user(mock_superadmin_user):
            result = await domain_resolver.admin_domain_fair_share.base_resolver(
                info=info,
                resource_group_name="default",
                domain_name="test-domain",
            )

        context.adapters.fair_share.get_domain.assert_called_once()
        call_arg = context.adapters.fair_share.get_domain.call_args[0][0]
        assert call_arg.resource_group == "default"
        assert call_arg.domain_name == "test-domain"

        assert isinstance(result, DomainFairShareGQL)
        assert result.resource_group_name == "default"
        assert result.domain_name == "test-domain"

    async def test_admin_domain_fair_share_propagates_entity_not_found(
        self,
        mock_superadmin_user: UserData,
    ) -> None:
        """Should propagate DomainNotFound from adapter."""
        context = MagicMock()
        context.adapters.fair_share.get_domain = AsyncMock(
            side_effect=DomainNotFound("Domain not found: nonexistent-domain")
        )
        info = create_mock_info(context)

        with with_user(mock_superadmin_user):
            with pytest.raises(DomainNotFound):
                await domain_resolver.admin_domain_fair_share.base_resolver(
                    info=info,
                    resource_group_name="default",
                    domain_name="nonexistent-domain",
                )

    async def test_admin_domain_fair_share_requires_admin(
        self,
        mock_regular_user: UserData,
    ) -> None:
        """Should raise HTTPForbidden for non-admin users."""
        context = MagicMock()
        context.adapters.fair_share.get_domain = AsyncMock()
        info = create_mock_info(context)

        with with_user(mock_regular_user):
            with pytest.raises(web.HTTPForbidden):
                await domain_resolver.admin_domain_fair_share.base_resolver(
                    info=info,
                    resource_group_name="default",
                    domain_name="test-domain",
                )

        context.adapters.fair_share.get_domain.assert_not_called()

    async def test_admin_domain_fair_share_returns_correct_gql_type(
        self,
        mock_superadmin_user: UserData,
        sample_domain_fair_share_data: DomainFairShareData,
    ) -> None:
        """Should return DomainFairShareGQL type with correct fields."""
        domain_node = FairShareAdapter._domain_data_to_dto(sample_domain_fair_share_data)
        context = MagicMock()
        context.adapters.fair_share.get_domain = AsyncMock(
            return_value=GetDomainFairSharePayload(item=domain_node)
        )
        info = create_mock_info(context)

        with with_user(mock_superadmin_user):
            result = await domain_resolver.admin_domain_fair_share.base_resolver(
                info=info,
                resource_group_name="default",
                domain_name="test-domain",
            )

        assert isinstance(result, DomainFairShareGQL)
        assert result.resource_group_name == sample_domain_fair_share_data.resource_group
        assert result.domain_name == sample_domain_fair_share_data.domain_name
        assert result.spec.weight == sample_domain_fair_share_data.data.spec.weight


# Admin List Query Tests


class TestAdminDomainFairSharesListQuery:
    async def test_admin_domain_fair_shares_calls_adapter_with_parameters(
        self,
        mock_superadmin_user: UserData,
    ) -> None:
        """Should call adapter with correct parameters."""
        context = MagicMock()
        context.adapters.fair_share.search_domain = AsyncMock(
            return_value=SearchDomainFairSharesPayload(items=[], total_count=0)
        )
        info = create_mock_info(context)

        with with_user(mock_superadmin_user):
            await domain_resolver.admin_domain_fair_shares.base_resolver(
                info=info,
                filter=None,
                order_by=None,
                before=None,
                after=None,
                first=None,
                last=None,
                limit=10,
                offset=0,
            )

        context.adapters.fair_share.search_domain.assert_called_once()
        input_dto = context.adapters.fair_share.search_domain.call_args[0][0]
        assert input_dto.limit == 10
        assert input_dto.offset == 0

    async def test_admin_domain_fair_shares_returns_connection_type(
        self,
        mock_superadmin_user: UserData,
    ) -> None:
        """Should return DomainFairShareConnection type."""
        context = MagicMock()
        context.adapters.fair_share.search_domain = AsyncMock(
            return_value=SearchDomainFairSharesPayload(items=[], total_count=0)
        )
        info = create_mock_info(context)

        with with_user(mock_superadmin_user):
            result = await domain_resolver.admin_domain_fair_shares.base_resolver(
                info=info,
                filter=None,
                order_by=None,
                before=None,
                after=None,
                first=None,
                last=None,
                limit=10,
                offset=0,
            )

        assert isinstance(result, DomainFairShareConnection)

    async def test_admin_domain_fair_shares_requires_admin(
        self,
        mock_regular_user: UserData,
    ) -> None:
        """Should raise HTTPForbidden for non-admin users."""
        context = MagicMock()
        context.adapters.fair_share.search_domain = AsyncMock()
        info = create_mock_info(context)

        with with_user(mock_regular_user):
            with pytest.raises(web.HTTPForbidden):
                await domain_resolver.admin_domain_fair_shares.base_resolver(
                    info=info,
                    filter=None,
                    order_by=None,
                    before=None,
                    after=None,
                    first=None,
                    last=None,
                    limit=10,
                    offset=0,
                )

        context.adapters.fair_share.search_domain.assert_not_called()

    async def test_admin_domain_fair_shares_handles_empty_results(
        self,
        mock_superadmin_user: UserData,
    ) -> None:
        """Should handle empty results gracefully."""
        context = MagicMock()
        context.adapters.fair_share.search_domain = AsyncMock(
            return_value=SearchDomainFairSharesPayload(items=[], total_count=0)
        )
        info = create_mock_info(context)

        with with_user(mock_superadmin_user):
            result = await domain_resolver.admin_domain_fair_shares.base_resolver(
                info=info,
                filter=None,
                order_by=None,
                before=None,
                after=None,
                first=None,
                last=None,
                limit=10,
                offset=0,
            )

        assert result.count == 0
        assert len(result.edges) == 0
