"""Tests for RG-scoped user fair share GraphQL resolvers."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.gql.fair_share.resolver import user as user_resolver
from ai.backend.manager.api.gql.fair_share.types import (
    UserFairShareGQL,
)
from ai.backend.manager.api.gql.types import ResourceGroupUserScope
from ai.backend.manager.data.fair_share import (
    FairShareCalculationSnapshot,
    FairShareData,
    FairShareMetadata,
    FairShareSpec,
    UserFairShareData,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.services.fair_share.actions import GetUserFairShareAction


class TestRGUserFairShare:
    """Tests for rg_user_fair_share resolver."""

    @pytest.fixture
    def project_id(self) -> UUID:
        """Test project ID."""
        return UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    @pytest.fixture
    def user_uuid(self) -> UUID:
        """Test user UUID."""
        return UUID("11111111-2222-3333-4444-555555555555")

    @pytest.fixture
    def user_fair_share_data(self, project_id: UUID, user_uuid: UUID) -> UserFairShareData:
        """User fair share data for existing record."""
        return UserFairShareData(
            resource_group="default",
            user_uuid=user_uuid,
            project_id=project_id,
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
            scheduling_rank=None,
        )

    @pytest.fixture
    def info_with_user_fair_share_exists(
        self, user_fair_share_data: UserFairShareData
    ) -> MagicMock:
        """Info context where user fair share exists."""
        info = MagicMock()
        action_result = MagicMock()
        action_result.data = user_fair_share_data
        info.context.processors.fair_share.get_user_fair_share.wait_for_complete = AsyncMock(
            return_value=action_result
        )
        return info

    @pytest.mark.asyncio
    async def test_returns_user_fair_share_when_exists(
        self,
        info_with_user_fair_share_exists: MagicMock,
        user_uuid: UUID,
    ) -> None:
        """Should return user fair share when it exists."""
        scope = ResourceGroupUserScope(
            resource_group_name="default",
            domain_name="test-domain",
            project_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        )

        resolver_fn = user_resolver.rg_user_fair_share.base_resolver
        result = await resolver_fn(
            info_with_user_fair_share_exists,
            scope,
            user_uuid,
        )

        assert result is not None
        assert isinstance(result, UserFairShareGQL)
        assert result.resource_group_name == "default"
        assert result.domain_name == "test-domain"

    @pytest.mark.asyncio
    async def test_calls_action_with_correct_params(
        self,
        info_with_user_fair_share_exists: MagicMock,
    ) -> None:
        """Should call action with correct resource_group, project_id, and user_uuid."""
        project_id = "11111111-2222-3333-4444-555555555555"
        user_uuid = UUID("66666666-7777-8888-9999-aaaaaaaaaaaa")

        scope = ResourceGroupUserScope(
            resource_group_name="custom-rg",
            domain_name="my-domain",
            project_id=project_id,
        )

        resolver_fn = user_resolver.rg_user_fair_share.base_resolver
        await resolver_fn(
            info_with_user_fair_share_exists,
            scope,
            user_uuid,
        )

        call_args = info_with_user_fair_share_exists.context.processors.fair_share.get_user_fair_share.wait_for_complete.call_args
        action = call_args[0][0]
        assert isinstance(action, GetUserFairShareAction)
        assert action.resource_group == "custom-rg"
        assert action.project_id == UUID(project_id)
        assert action.user_uuid == user_uuid

    @pytest.fixture
    def info_with_user_not_found(self) -> MagicMock:
        """Info context where user does not exist."""
        info = MagicMock()
        info.context.processors.fair_share.get_user_fair_share.wait_for_complete = AsyncMock(
            side_effect=UserNotFound()
        )
        return info

    @pytest.mark.asyncio
    async def test_raises_user_not_found_when_user_does_not_exist(
        self,
        info_with_user_not_found: MagicMock,
    ) -> None:
        """Should raise UserNotFound when user does not exist."""
        scope = ResourceGroupUserScope(
            resource_group_name="default",
            domain_name="test-domain",
            project_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        )
        user_uuid = UUID("11111111-2222-3333-4444-555555555555")

        resolver_fn = user_resolver.rg_user_fair_share.base_resolver
        with pytest.raises(UserNotFound):
            await resolver_fn(
                info_with_user_not_found,
                scope,
                user_uuid,
            )


class TestRGUserFairShares:
    """Tests for rg_user_fair_shares resolver."""

    @pytest.mark.asyncio
    async def test_calls_fetch_rg_user_fair_shares(self) -> None:
        """Should call fetch_rg_user_fair_shares with correct scope."""
        info = MagicMock()
        scope = ResourceGroupUserScope(
            resource_group_name="default",
            domain_name="test-domain",
            project_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        )
        mock_connection = MagicMock()

        with patch(
            "ai.backend.manager.api.gql.fair_share.resolver.user.fetch_rg_user_fair_shares",
            new_callable=AsyncMock,
            return_value=mock_connection,
        ) as mock_fetch:
            resolver_fn = user_resolver.rg_user_fair_shares.base_resolver
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
            assert call_kwargs["scope"].domain_name == "test-domain"
            assert call_kwargs["first"] == 10
