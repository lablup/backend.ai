"""Tests for RG-scoped domain fair share GraphQL resolvers."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.gql.fair_share.resolver import domain as domain_resolver
from ai.backend.manager.api.gql.fair_share.types import (
    DomainFairShareGQL,
)
from ai.backend.manager.api.gql.types import ResourceGroupDomainScope
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    FairShareCalculationSnapshot,
    FairShareData,
    FairShareMetadata,
    FairShareSpec,
)
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.services.fair_share.actions import GetDomainFairShareAction


class TestRGDomainFairShare:
    """Tests for rg_domain_fair_share resolver."""

    @pytest.fixture
    def domain_fair_share_data(self) -> DomainFairShareData:
        """Domain fair share data for existing record."""
        return DomainFairShareData(
            resource_group="default",
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("2.0"),
                    half_life_days=14,
                    lookback_days=30,
                    decay_unit_days=1,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=Decimal("0.5"),
                    total_decayed_usage=ResourceSlot({"cpu": Decimal("50.0")}),
                    normalized_usage=Decimal("100.0"),
                    lookback_start=date(2024, 1, 1),
                    lookback_end=date(2024, 1, 31),
                    last_calculated_at=datetime(2024, 1, 31, 12, 0, 0, tzinfo=UTC),
                ),
                metadata=FairShareMetadata(
                    created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
                    updated_at=datetime(2024, 1, 31, 12, 0, 0, tzinfo=UTC),
                ),
                use_default=False,
            ),
        )

    @pytest.fixture
    def info_with_domain_fair_share_exists(
        self, domain_fair_share_data: DomainFairShareData
    ) -> MagicMock:
        """Info context where domain fair share exists."""
        info = MagicMock()
        action_result = MagicMock()
        action_result.data = domain_fair_share_data
        info.context.processors.fair_share.get_domain_fair_share.wait_for_complete = AsyncMock(
            return_value=action_result
        )
        return info

    @pytest.mark.asyncio
    async def test_returns_domain_fair_share_when_exists(
        self,
        info_with_domain_fair_share_exists: MagicMock,
    ) -> None:
        """Should return domain fair share when it exists."""
        scope = ResourceGroupDomainScope(resource_group="default")

        resolver_fn = domain_resolver.rg_domain_fair_share.base_resolver
        result = await resolver_fn(
            info_with_domain_fair_share_exists,
            scope,
            "test-domain",
        )

        assert result is not None
        assert isinstance(result, DomainFairShareGQL)
        assert result.domain_name == "test-domain"
        assert result.resource_group_name == "default"

    @pytest.mark.asyncio
    async def test_calls_action_with_correct_params(
        self,
        info_with_domain_fair_share_exists: MagicMock,
    ) -> None:
        """Should call action with correct resource_group and domain_name."""
        scope = ResourceGroupDomainScope(resource_group="custom-rg")

        resolver_fn = domain_resolver.rg_domain_fair_share.base_resolver
        await resolver_fn(
            info_with_domain_fair_share_exists,
            scope,
            "my-domain",
        )

        call_args = info_with_domain_fair_share_exists.context.processors.fair_share.get_domain_fair_share.wait_for_complete.call_args
        action = call_args[0][0]
        assert isinstance(action, GetDomainFairShareAction)
        assert action.resource_group == "custom-rg"
        assert action.domain_name == "my-domain"

    @pytest.fixture
    def info_with_domain_not_found(self) -> MagicMock:
        """Info context where domain does not exist."""
        info = MagicMock()
        info.context.processors.fair_share.get_domain_fair_share.wait_for_complete = AsyncMock(
            side_effect=DomainNotFound()
        )
        return info

    @pytest.mark.asyncio
    async def test_raises_domain_not_found_when_domain_does_not_exist(
        self,
        info_with_domain_not_found: MagicMock,
    ) -> None:
        """Should raise DomainNotFound when domain does not exist."""
        scope = ResourceGroupDomainScope(resource_group="default")

        resolver_fn = domain_resolver.rg_domain_fair_share.base_resolver
        with pytest.raises(DomainNotFound):
            await resolver_fn(
                info_with_domain_not_found,
                scope,
                "nonexistent-domain",
            )


class TestRGDomainFairShares:
    """Tests for rg_domain_fair_shares resolver."""

    @pytest.mark.asyncio
    async def test_calls_fetch_rg_domain_fair_shares(self) -> None:
        """Should call fetch_rg_domain_fair_shares with correct scope."""
        info = MagicMock()
        scope = ResourceGroupDomainScope(resource_group="default")
        mock_connection = MagicMock()

        with patch(
            "ai.backend.manager.api.gql.fair_share.resolver.domain.fetch_rg_domain_fair_shares",
            new_callable=AsyncMock,
            return_value=mock_connection,
        ) as mock_fetch:
            resolver_fn = domain_resolver.rg_domain_fair_shares.base_resolver
            result = await resolver_fn(
                info,
                scope,
                None,  # filter
                None,  # order_by
                None,  # before
                None,  # after
                10,  # first
                None,  # last
                None,  # limit
                None,  # offset
            )

            assert result == mock_connection
            mock_fetch.assert_called_once()
            call_kwargs = mock_fetch.call_args.kwargs
            assert call_kwargs["info"] == info
            assert call_kwargs["scope"].resource_group == "default"
            assert call_kwargs["first"] == 10
