"""Tests for Domain Fair Share GQL query resolvers."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from aiohttp import web

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import ResourceSlot
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
from ai.backend.manager.services.fair_share.actions import (
    GetDomainFairShareAction,
    GetDomainFairShareActionResult,
)

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
def mock_get_domain_processor() -> AsyncMock:
    """Create mock get_domain_fair_share processor."""
    processor = AsyncMock()
    processor.wait_for_complete = AsyncMock()
    return processor


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
                total_decayed_usage=ResourceSlot({
                    "cpu": Decimal("100.0"),
                    "mem": Decimal("200.0"),
                }),
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


def create_mock_context(get_domain_processor: AsyncMock | None = None) -> MagicMock:
    """Create mock GraphQL context with processors."""
    context = MagicMock()
    context.processors = MagicMock()
    context.processors.fair_share = MagicMock()

    if get_domain_processor:
        context.processors.fair_share.get_domain_fair_share = get_domain_processor

    return context


def create_mock_info(context: MagicMock) -> MagicMock:
    """Create mock strawberry.Info with context."""
    info = MagicMock()
    info.context = context
    return info


# Admin Single Query Tests


class TestAdminDomainFairShareSingleQuery:
    @pytest.mark.asyncio
    async def test_admin_domain_fair_share_calls_processor_with_correct_action(
        self,
        mock_superadmin_user: UserData,
        mock_get_domain_processor: AsyncMock,
        sample_domain_fair_share_data: DomainFairShareData,
    ) -> None:
        """Should call processor with correct GetDomainFairShareAction."""
        mock_get_domain_processor.wait_for_complete.return_value = GetDomainFairShareActionResult(
            data=sample_domain_fair_share_data
        )
        context = create_mock_context(get_domain_processor=mock_get_domain_processor)
        info = create_mock_info(context)

        with with_user(mock_superadmin_user):
            result = await domain_resolver.admin_domain_fair_share.base_resolver(
                info=info,
                resource_group="default",
                domain_name="test-domain",
            )

        # Should call processor with correct action
        mock_get_domain_processor.wait_for_complete.assert_called_once()
        call_args = mock_get_domain_processor.wait_for_complete.call_args
        action = call_args[0][0]
        assert isinstance(action, GetDomainFairShareAction)
        assert action.resource_group == "default"
        assert action.domain_name == "test-domain"

        # Should return DomainFairShareGQL
        assert isinstance(result, DomainFairShareGQL)
        assert result.resource_group == "default"
        assert result.domain_name == "test-domain"

    @pytest.mark.asyncio
    async def test_admin_domain_fair_share_propagates_entity_not_found(
        self,
        mock_superadmin_user: UserData,
        mock_get_domain_processor: AsyncMock,
    ) -> None:
        """Should propagate DomainNotFound from service."""
        mock_get_domain_processor.wait_for_complete.side_effect = DomainNotFound(
            "Domain not found: nonexistent-domain"
        )
        context = create_mock_context(get_domain_processor=mock_get_domain_processor)
        info = create_mock_info(context)

        with with_user(mock_superadmin_user):
            with pytest.raises(DomainNotFound):
                await domain_resolver.admin_domain_fair_share.base_resolver(
                    info=info,
                    resource_group="default",
                    domain_name="nonexistent-domain",
                )

    @pytest.mark.asyncio
    async def test_admin_domain_fair_share_requires_admin(
        self,
        mock_regular_user: UserData,
        mock_get_domain_processor: AsyncMock,
    ) -> None:
        """Should raise HTTPForbidden for non-admin users."""
        context = create_mock_context(get_domain_processor=mock_get_domain_processor)
        info = create_mock_info(context)

        with with_user(mock_regular_user):
            with pytest.raises(web.HTTPForbidden):
                await domain_resolver.admin_domain_fair_share.base_resolver(
                    info=info,
                    resource_group="default",
                    domain_name="test-domain",
                )

        # Should not call processor
        mock_get_domain_processor.wait_for_complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_admin_domain_fair_share_returns_correct_gql_type(
        self,
        mock_superadmin_user: UserData,
        mock_get_domain_processor: AsyncMock,
        sample_domain_fair_share_data: DomainFairShareData,
    ) -> None:
        """Should return DomainFairShareGQL type with correct fields."""
        mock_get_domain_processor.wait_for_complete.return_value = GetDomainFairShareActionResult(
            data=sample_domain_fair_share_data
        )
        context = create_mock_context(get_domain_processor=mock_get_domain_processor)
        info = create_mock_info(context)

        with with_user(mock_superadmin_user):
            result = await domain_resolver.admin_domain_fair_share.base_resolver(
                info=info,
                resource_group="default",
                domain_name="test-domain",
            )

        assert isinstance(result, DomainFairShareGQL)
        assert (
            result.id
            == f"{sample_domain_fair_share_data.resource_group}:{sample_domain_fair_share_data.domain_name}"
        )
        assert result.resource_group == sample_domain_fair_share_data.resource_group
        assert result.domain_name == sample_domain_fair_share_data.domain_name
        assert result.spec.weight == sample_domain_fair_share_data.data.spec.weight


# Admin List Query Tests


class TestAdminDomainFairSharesListQuery:
    @pytest.mark.asyncio
    async def test_admin_domain_fair_shares_calls_fetcher_with_parameters(
        self,
        mock_superadmin_user: UserData,
    ) -> None:
        """Should call fetch_domain_fair_shares with correct parameters."""
        mock_fetcher = AsyncMock(
            return_value=DomainFairShareConnection(
                edges=[],
                count=0,
                page_info=MagicMock(),
            )
        )

        with with_user(mock_superadmin_user):
            with patch.object(
                domain_resolver, "fetch_domain_fair_shares", mock_fetcher
            ) as patched_fetcher:
                info = create_mock_info(MagicMock())
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

                # Should call fetcher with correct parameters
                patched_fetcher.assert_called_once()
                call_kwargs = patched_fetcher.call_args[1]
                assert call_kwargs["limit"] == 10
                assert call_kwargs["offset"] == 0

    @pytest.mark.asyncio
    async def test_admin_domain_fair_shares_returns_connection_type(
        self,
        mock_superadmin_user: UserData,
    ) -> None:
        """Should return DomainFairShareConnection type."""
        mock_fetcher = AsyncMock(
            return_value=DomainFairShareConnection(
                edges=[],
                count=0,
                page_info=MagicMock(),
            )
        )

        with with_user(mock_superadmin_user):
            with patch.object(domain_resolver, "fetch_domain_fair_shares", mock_fetcher):
                info = create_mock_info(MagicMock())
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

    @pytest.mark.asyncio
    async def test_admin_domain_fair_shares_requires_admin(
        self,
        mock_regular_user: UserData,
    ) -> None:
        """Should raise HTTPForbidden for non-admin users."""
        mock_fetcher = AsyncMock()

        with with_user(mock_regular_user):
            with patch.object(domain_resolver, "fetch_domain_fair_shares", mock_fetcher):
                info = create_mock_info(MagicMock())
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

                # Should not call fetcher
                mock_fetcher.assert_not_called()

    @pytest.mark.asyncio
    async def test_admin_domain_fair_shares_handles_empty_results(
        self,
        mock_superadmin_user: UserData,
    ) -> None:
        """Should handle empty results gracefully."""
        mock_fetcher = AsyncMock(
            return_value=DomainFairShareConnection(
                edges=[],
                count=0,
                page_info=MagicMock(),
            )
        )

        with with_user(mock_superadmin_user):
            with patch.object(domain_resolver, "fetch_domain_fair_shares", mock_fetcher):
                info = create_mock_info(MagicMock())
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
