"""Tests for FairShareService."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    DomainFairShareSearchResult,
    FairShareCalculationSnapshot,
    FairShareMetadata,
    FairShareSpec,
    ProjectFairShareData,
    ProjectFairShareSearchResult,
    UserFairShareData,
    UserFairShareSearchResult,
)
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.repositories.fair_share.types import (
    DomainFairShareEntityItem,
    DomainFairShareEntitySearchResult,
    DomainFairShareSearchScope,
    ProjectFairShareEntityItem,
    ProjectFairShareEntitySearchResult,
    ProjectFairShareSearchScope,
    UserFairShareEntityItem,
    UserFairShareEntitySearchResult,
    UserFairShareSearchScope,
)
from ai.backend.manager.services.fair_share import (
    FairShareService,
    GetDomainFairShareAction,
    GetProjectFairShareAction,
    GetUserFairShareAction,
    SearchDomainFairSharesAction,
    SearchProjectFairSharesAction,
    SearchRGDomainFairSharesAction,
    SearchRGProjectFairSharesAction,
    SearchRGUserFairSharesAction,
    SearchUserFairSharesAction,
)


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=FairShareRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> FairShareService:
    return FairShareService(repository=mock_repository)


# Domain Fair Share Tests


class TestGetDomainFairShare:
    @pytest.mark.asyncio
    async def test_get_domain_fair_share_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with correct parameters."""
        expected_data = MagicMock(spec=DomainFairShareData)
        expected_data.id = uuid.uuid4()
        mock_repository.get_domain_fair_share = AsyncMock(return_value=expected_data)

        action = GetDomainFairShareAction(
            resource_group="default",
            domain_name="test-domain",
        )

        result = await service.get_domain_fair_share(action)

        mock_repository.get_domain_fair_share.assert_called_once_with(
            resource_group="default",
            domain_name="test-domain",
        )
        assert result.data == expected_data


class TestSearchDomainFairShares:
    @pytest.mark.asyncio
    async def test_search_domain_fair_shares_returns_result(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return search results from repository."""
        mock_fair_share = MagicMock(spec=DomainFairShareData)
        mock_result = DomainFairShareSearchResult(
            items=[mock_fair_share],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_domain_fair_shares = AsyncMock(return_value=mock_result)

        action = SearchDomainFairSharesAction(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[],
            orders=[],
        )

        result = await service.search_domain_fair_shares(action)

        mock_repository.search_domain_fair_shares.assert_called_once()
        assert result.items == [mock_fair_share]
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_domain_fair_shares_passes_querier(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create BatchQuerier with correct parameters."""
        mock_result = DomainFairShareSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_domain_fair_shares = AsyncMock(return_value=mock_result)

        pagination = OffsetPagination(offset=0, limit=20)
        action = SearchDomainFairSharesAction(
            pagination=pagination,
            conditions=[],
            orders=[],
        )

        await service.search_domain_fair_shares(action)

        call_args = mock_repository.search_domain_fair_shares.call_args
        querier = call_args[0][0]

        assert querier.conditions == []
        assert querier.orders == []
        assert querier.pagination == pagination


# Project Fair Share Tests


class TestGetProjectFairShare:
    @pytest.mark.asyncio
    async def test_get_project_fair_share_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with correct parameters."""
        project_id = uuid.uuid4()
        expected_data = MagicMock(spec=ProjectFairShareData)
        expected_data.id = uuid.uuid4()
        mock_repository.get_project_fair_share = AsyncMock(return_value=expected_data)

        action = GetProjectFairShareAction(
            resource_group="default",
            project_id=project_id,
        )

        result = await service.get_project_fair_share(action)

        mock_repository.get_project_fair_share.assert_called_once_with(
            resource_group="default",
            project_id=project_id,
        )
        assert result.data == expected_data


class TestSearchProjectFairShares:
    @pytest.mark.asyncio
    async def test_search_project_fair_shares_returns_result(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return search results from repository."""
        mock_fair_share = MagicMock(spec=ProjectFairShareData)
        mock_result = ProjectFairShareSearchResult(
            items=[mock_fair_share],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_project_fair_shares = AsyncMock(return_value=mock_result)

        action = SearchProjectFairSharesAction(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[],
            orders=[],
        )

        result = await service.search_project_fair_shares(action)

        mock_repository.search_project_fair_shares.assert_called_once()
        assert result.items == [mock_fair_share]
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_project_fair_shares_passes_querier(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create BatchQuerier with correct parameters."""
        mock_result = ProjectFairShareSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_project_fair_shares = AsyncMock(return_value=mock_result)

        pagination = OffsetPagination(offset=0, limit=20)
        action = SearchProjectFairSharesAction(
            pagination=pagination,
            conditions=[],
            orders=[],
        )

        await service.search_project_fair_shares(action)

        call_args = mock_repository.search_project_fair_shares.call_args
        querier = call_args[0][0]

        assert querier.conditions == []
        assert querier.orders == []
        assert querier.pagination == pagination


# User Fair Share Tests


class TestGetUserFairShare:
    @pytest.mark.asyncio
    async def test_get_user_fair_share_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with correct parameters."""
        project_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        expected_data = MagicMock(spec=UserFairShareData)
        expected_data.id = uuid.uuid4()
        mock_repository.get_user_fair_share = AsyncMock(return_value=expected_data)

        action = GetUserFairShareAction(
            resource_group="default",
            project_id=project_id,
            user_uuid=user_uuid,
        )

        result = await service.get_user_fair_share(action)

        mock_repository.get_user_fair_share.assert_called_once_with(
            resource_group="default",
            project_id=project_id,
            user_uuid=user_uuid,
        )
        assert result.data == expected_data


class TestSearchUserFairShares:
    @pytest.mark.asyncio
    async def test_search_user_fair_shares_returns_result(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return search results from repository."""
        mock_fair_share = MagicMock(spec=UserFairShareData)
        mock_result = UserFairShareSearchResult(
            items=[mock_fair_share],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_user_fair_shares = AsyncMock(return_value=mock_result)

        action = SearchUserFairSharesAction(
            pagination=OffsetPagination(offset=0, limit=10),
            conditions=[],
            orders=[],
        )

        result = await service.search_user_fair_shares(action)

        mock_repository.search_user_fair_shares.assert_called_once()
        assert result.items == [mock_fair_share]
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_user_fair_shares_passes_querier(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create BatchQuerier with correct parameters."""
        mock_result = UserFairShareSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_user_fair_shares = AsyncMock(return_value=mock_result)

        pagination = OffsetPagination(offset=0, limit=20)
        action = SearchUserFairSharesAction(
            pagination=pagination,
            conditions=[],
            orders=[],
        )

        await service.search_user_fair_shares(action)

        call_args = mock_repository.search_user_fair_shares.call_args
        querier = call_args[0][0]

        assert querier.conditions == []
        assert querier.orders == []
        assert querier.pagination == pagination


# Entity Search Tests


class TestSearchDomainFairShareEntities:
    @pytest.mark.asyncio
    async def test_includes_entities_with_and_without_records(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Include domains both with and without fair share records."""
        # Mock domain with record
        domain_with_record = DomainFairShareData(
            id=uuid.uuid4(),
            resource_group="default",
            domain_name="domain-with-record",
            spec=FairShareSpec(
                weight=Decimal("2.0"),
                half_life_days=14,
                lookback_days=30,
                decay_unit_days=1,
                resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
            ),
            calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
            metadata=MagicMock(spec=FairShareMetadata),
            default_weight=Decimal("1.0"),
        )

        # Mock entity items (one with details, one without)
        entity_items = [
            DomainFairShareEntityItem(
                resource_group="default",
                domain_name="domain-with-record",
                details=domain_with_record,
            ),
            DomainFairShareEntityItem(
                resource_group="default",
                domain_name="domain-without-record",
                details=None,  # No record
            ),
        ]

        entity_result = DomainFairShareEntitySearchResult(
            items=entity_items,
            total_count=2,
            has_next_page=False,
            has_previous_page=False,
        )

        mock_repository.search_domain_fair_share_entities = AsyncMock(return_value=entity_result)
        mock_repository.get_scaling_group_fair_share_spec = AsyncMock(
            return_value=FairShareScalingGroupSpec(
                default_weight=Decimal("1.0"),
                half_life_days=14,
                lookback_days=30,
                decay_unit_days=1,
                resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
            )
        )

        scope = DomainFairShareSearchScope(resource_group="default")
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=0, limit=100),
            conditions=[],
            orders=[],
        )
        action = SearchRGDomainFairSharesAction(scope=scope, querier=querier)
        result = await service.search_rg_domain_fair_shares(action)

        # Both domains should be included
        assert result.total_count == 2
        assert len(result.items) == 2

        # One with persisted record (non-zero UUID)
        assert any(item.id != uuid.UUID(int=0) for item in result.items)
        # One with default (sentinel UUID)
        assert any(item.id == uuid.UUID(int=0) for item in result.items)

    @pytest.mark.asyncio
    async def test_default_has_weight_none(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Default values have weight=None."""
        entity_items = [
            DomainFairShareEntityItem(
                resource_group="default",
                domain_name="domain-without-record",
                details=None,  # No record
            ),
        ]

        entity_result = DomainFairShareEntitySearchResult(
            items=entity_items,
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

        mock_repository.search_domain_fair_share_entities = AsyncMock(return_value=entity_result)
        mock_repository.get_scaling_group_fair_share_spec = AsyncMock(
            return_value=FairShareScalingGroupSpec(
                default_weight=Decimal("1.0"),
                half_life_days=14,
                lookback_days=30,
                decay_unit_days=1,
                resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
            )
        )

        scope = DomainFairShareSearchScope(resource_group="default")
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=0, limit=100),
            conditions=[],
            orders=[],
        )
        action = SearchRGDomainFairSharesAction(scope=scope, querier=querier)
        result = await service.search_rg_domain_fair_shares(action)

        # Domain without record (id=0)
        default_domain = [item for item in result.items if item.id == uuid.UUID(int=0)][0]
        assert default_domain.spec.weight is None

    @pytest.mark.asyncio
    async def test_default_matches_scaling_group_spec(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Default values match scaling group settings."""
        entity_items = [
            DomainFairShareEntityItem(
                resource_group="default",
                domain_name="domain-without-record",
                details=None,
            ),
        ]

        entity_result = DomainFairShareEntitySearchResult(
            items=entity_items,
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

        # Custom scaling group spec
        custom_spec = FairShareScalingGroupSpec(
            default_weight=Decimal("2.5"),
            half_life_days=7,
            lookback_days=60,
            decay_unit_days=2,
            resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.5")}),
        )

        mock_repository.search_domain_fair_share_entities = AsyncMock(return_value=entity_result)
        mock_repository.get_scaling_group_fair_share_spec = AsyncMock(return_value=custom_spec)

        scope = DomainFairShareSearchScope(resource_group="default")
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=0, limit=100),
            conditions=[],
            orders=[],
        )
        action = SearchRGDomainFairSharesAction(scope=scope, querier=querier)
        result = await service.search_rg_domain_fair_shares(action)

        default_domain = result.items[0]
        # Verify defaults use scaling group spec
        assert default_domain.spec.half_life_days == 7
        assert default_domain.spec.lookback_days == 60
        assert default_domain.spec.decay_unit_days == 2
        assert default_domain.spec.resource_weights == ResourceSlot({
            "cpu": Decimal("1.0"),
            "mem": Decimal("0.5"),
        })
        assert default_domain.default_weight == Decimal("2.5")


class TestSearchProjectFairShareEntities:
    @pytest.mark.asyncio
    async def test_includes_entities_with_and_without_records(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Include projects both with and without fair share records."""
        project_id_with_record = uuid.uuid4()
        project_id_without_record = uuid.uuid4()

        # Mock project with record
        project_with_record = ProjectFairShareData(
            id=uuid.uuid4(),
            resource_group="default",
            project_id=project_id_with_record,
            domain_name="test-domain",
            spec=FairShareSpec(
                weight=Decimal("2.0"),
                half_life_days=14,
                lookback_days=30,
                decay_unit_days=1,
                resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
            ),
            calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
            metadata=MagicMock(spec=FairShareMetadata),
            default_weight=Decimal("1.0"),
        )

        # Mock entity items
        entity_items = [
            ProjectFairShareEntityItem(
                resource_group="default",
                project_id=project_id_with_record,
                domain_name="test-domain",
                details=project_with_record,
            ),
            ProjectFairShareEntityItem(
                resource_group="default",
                project_id=project_id_without_record,
                domain_name="test-domain",
                details=None,
            ),
        ]

        entity_result = ProjectFairShareEntitySearchResult(
            items=entity_items,
            total_count=2,
            has_next_page=False,
            has_previous_page=False,
        )

        mock_repository.search_project_fair_share_entities = AsyncMock(return_value=entity_result)
        mock_repository.get_scaling_group_fair_share_spec = AsyncMock(
            return_value=FairShareScalingGroupSpec(
                default_weight=Decimal("1.0"),
                half_life_days=14,
                lookback_days=30,
                decay_unit_days=1,
                resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
            )
        )

        scope = ProjectFairShareSearchScope(resource_group="default", domain_name="test-domain")
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=0, limit=100),
            conditions=[],
            orders=[],
        )
        action = SearchRGProjectFairSharesAction(scope=scope, querier=querier)
        result = await service.search_rg_project_fair_shares(action)

        assert result.total_count == 2
        assert len(result.items) == 2
        assert any(item.id != uuid.UUID(int=0) for item in result.items)
        assert any(item.id == uuid.UUID(int=0) for item in result.items)


class TestSearchUserFairShareEntities:
    @pytest.mark.asyncio
    async def test_includes_entities_with_and_without_records(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Include users both with and without fair share records."""
        user_uuid_with_record = uuid.uuid4()
        user_uuid_without_record = uuid.uuid4()
        project_id = uuid.uuid4()

        # Mock user with record
        user_with_record = UserFairShareData(
            id=uuid.uuid4(),
            resource_group="default",
            user_uuid=user_uuid_with_record,
            project_id=project_id,
            domain_name="test-domain",
            spec=FairShareSpec(
                weight=Decimal("2.0"),
                half_life_days=14,
                lookback_days=30,
                decay_unit_days=1,
                resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
            ),
            calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
            metadata=MagicMock(spec=FairShareMetadata),
            default_weight=Decimal("1.0"),
            scheduling_rank=None,
        )

        # Mock entity items
        entity_items = [
            UserFairShareEntityItem(
                resource_group="default",
                user_uuid=user_uuid_with_record,
                project_id=project_id,
                domain_name="test-domain",
                details=user_with_record,
            ),
            UserFairShareEntityItem(
                resource_group="default",
                user_uuid=user_uuid_without_record,
                project_id=project_id,
                domain_name="test-domain",
                details=None,
            ),
        ]

        entity_result = UserFairShareEntitySearchResult(
            items=entity_items,
            total_count=2,
            has_next_page=False,
            has_previous_page=False,
        )

        mock_repository.search_user_fair_share_entities = AsyncMock(return_value=entity_result)
        mock_repository.get_scaling_group_fair_share_spec = AsyncMock(
            return_value=FairShareScalingGroupSpec(
                default_weight=Decimal("1.0"),
                half_life_days=14,
                lookback_days=30,
                decay_unit_days=1,
                resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
            )
        )

        scope = UserFairShareSearchScope(
            resource_group="default",
            domain_name="test-domain",
            project_id=project_id,
        )
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=0, limit=100),
            conditions=[],
            orders=[],
        )
        action = SearchRGUserFairSharesAction(scope=scope, querier=querier)
        result = await service.search_rg_user_fair_shares(action)

        assert result.total_count == 2
        assert len(result.items) == 2
        assert any(item.id != uuid.UUID(int=0) for item in result.items)
        assert any(item.id == uuid.UUID(int=0) for item in result.items)
