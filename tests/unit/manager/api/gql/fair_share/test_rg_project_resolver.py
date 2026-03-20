"""Tests for RG-scoped project fair share GraphQL resolvers."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.fair_share.response import (
    GetProjectFairSharePayload,
    SearchProjectFairSharesPayload,
)
from ai.backend.common.types import ResourceSlot, SlotQuantity
from ai.backend.manager.api.adapters.fair_share import FairShareAdapter
from ai.backend.manager.api.gql.fair_share.resolver import project as project_resolver
from ai.backend.manager.api.gql.fair_share.types import (
    ProjectFairShareGQL,
)
from ai.backend.manager.api.gql.types import ResourceGroupProjectScope
from ai.backend.manager.data.fair_share import (
    FairShareCalculationSnapshot,
    FairShareData,
    FairShareMetadata,
    FairShareSpec,
    ProjectFairShareData,
)
from ai.backend.manager.errors.resource import ProjectNotFound


class TestRGProjectFairShare:
    """Tests for rg_project_fair_share resolver."""

    @pytest.fixture
    def project_id(self) -> UUID:
        """Test project ID."""
        return UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    @pytest.fixture
    def project_fair_share_data(self, project_id: UUID) -> ProjectFairShareData:
        """Project fair share data for existing record."""
        return ProjectFairShareData(
            resource_group="default",
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
                    total_decayed_usage=[SlotQuantity(slot_name="cpu", quantity=Decimal("50.0"))],
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
    def info_with_project_fair_share_exists(
        self, project_fair_share_data: ProjectFairShareData
    ) -> MagicMock:
        """Info context where project fair share exists."""
        project_node = FairShareAdapter._project_data_to_dto(project_fair_share_data)
        info = MagicMock()
        info.context.adapters.fair_share.get_project = AsyncMock(
            return_value=GetProjectFairSharePayload(item=project_node)
        )
        return info

    async def test_returns_project_fair_share_when_exists(
        self,
        info_with_project_fair_share_exists: MagicMock,
        project_id: UUID,
    ) -> None:
        """Should return project fair share when it exists."""
        scope = ResourceGroupProjectScope(resource_group_name="default", domain_name="test-domain")

        resolver_fn = project_resolver.rg_project_fair_share.base_resolver
        result = await resolver_fn(
            info_with_project_fair_share_exists,
            scope,
            project_id,
        )

        assert result is not None
        assert isinstance(result, ProjectFairShareGQL)
        assert result.resource_group_name == "default"
        assert result.domain_name == "test-domain"

    async def test_calls_adapter_with_correct_params(
        self,
        info_with_project_fair_share_exists: MagicMock,
    ) -> None:
        """Should call adapter with correct resource_group and project_id."""
        scope = ResourceGroupProjectScope(resource_group_name="custom-rg", domain_name="my-domain")
        project_id = UUID("11111111-2222-3333-4444-555555555555")

        resolver_fn = project_resolver.rg_project_fair_share.base_resolver
        await resolver_fn(
            info_with_project_fair_share_exists,
            scope,
            project_id,
        )

        call_arg = (
            info_with_project_fair_share_exists.context.adapters.fair_share.get_project.call_args[
                0
            ][0]
        )
        assert call_arg.resource_group == "custom-rg"
        assert call_arg.project_id == project_id

    @pytest.fixture
    def info_with_project_not_found(self) -> MagicMock:
        """Info context where project does not exist."""
        info = MagicMock()
        info.context.adapters.fair_share.get_project = AsyncMock(side_effect=ProjectNotFound())
        return info

    async def test_raises_project_not_found_when_project_does_not_exist(
        self,
        info_with_project_not_found: MagicMock,
    ) -> None:
        """Should raise ProjectNotFound when project does not exist."""
        scope = ResourceGroupProjectScope(resource_group_name="default", domain_name="test-domain")
        project_id = UUID("11111111-2222-3333-4444-555555555555")

        resolver_fn = project_resolver.rg_project_fair_share.base_resolver
        with pytest.raises(ProjectNotFound):
            await resolver_fn(
                info_with_project_not_found,
                scope,
                project_id,
            )


class TestRGProjectFairShares:
    """Tests for rg_project_fair_shares resolver."""

    async def test_calls_adapter_with_correct_scope(self) -> None:
        """Should call adapter with correct resource_group and domain_name."""
        info = MagicMock()
        info.context.adapters.fair_share.search_rg_project = AsyncMock(
            return_value=SearchProjectFairSharesPayload(items=[], total_count=0)
        )
        scope = ResourceGroupProjectScope(resource_group_name="default", domain_name="test-domain")

        resolver_fn = project_resolver.rg_project_fair_shares.base_resolver
        await resolver_fn(
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

        info.context.adapters.fair_share.search_rg_project.assert_called_once()
        call_args = info.context.adapters.fair_share.search_rg_project.call_args
        assert call_args[0][0].first == 10
        assert call_args.kwargs["resource_group"] == "default"
        assert call_args.kwargs["domain_name"] == "test-domain"
