"""Tests for FairShareService."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import ResourceSlot, SlotQuantity
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    DomainFairShareSearchResult,
    FairShareCalculationSnapshot,
    FairShareData,
    FairShareMetadata,
    FairShareSpec,
    ProjectFairShareData,
    ProjectFairShareSearchResult,
    UserFairShareData,
    UserFairShareSearchResult,
)
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.repositories.fair_share.types import (
    DomainFairShareEntitySearchResult,
    DomainFairShareSearchScope,
    ProjectFairShareEntitySearchResult,
    ProjectFairShareSearchScope,
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

    @pytest.mark.asyncio
    async def test_get_domain_fair_share_returns_default_when_not_found_but_exists(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """When record not found but domain exists, repository returns default values."""
        now = datetime.now(UTC)
        today = now.date()
        # Repository now creates and returns complete default data internally
        default_data = DomainFairShareData(
            resource_group="default",
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("2.0"),  # Repository sets default_weight here
                    half_life_days=7,
                    lookback_days=60,
                    decay_unit_days=2,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.5")}),
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=[
                        SlotQuantity("cpu", Decimal("0.0")),
                        SlotQuantity("mem", Decimal("0.0")),
                    ],
                    normalized_usage=Decimal("0.0"),
                    lookback_start=today,
                    lookback_end=today,
                    last_calculated_at=now,
                ),
                metadata=None,  # No metadata for default-generated records
                use_default=True,  # True for default-generated records
            ),
        )
        mock_repository.get_domain_fair_share = AsyncMock(return_value=default_data)

        action = GetDomainFairShareAction(
            resource_group="default",
            domain_name="test-domain",
        )

        result = await service.get_domain_fair_share(action)

        # Service should just return the result from repository
        assert result.data == default_data
        assert result.data.data.spec.weight == Decimal("2.0")  # Repository sets default_weight
        assert result.data.data.use_default is True

    @pytest.mark.asyncio
    async def test_get_domain_fair_share_raises_entity_not_found_when_entity_missing(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """When domain doesn't exist, repository should raise DomainNotFound."""
        # Repository raises DomainNotFound directly when domain doesn't exist
        mock_repository.get_domain_fair_share = AsyncMock(
            side_effect=DomainNotFound("Domain not found: nonexistent-domain")
        )

        action = GetDomainFairShareAction(
            resource_group="default",
            domain_name="nonexistent-domain",
        )

        with pytest.raises(DomainNotFound):
            await service.get_domain_fair_share(action)

    @pytest.mark.asyncio
    async def test_get_domain_fair_share_uses_scaling_group_spec_for_default(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Default values from repository should reflect custom scaling group spec settings."""
        now = datetime.now(UTC)
        today = now.date()
        # Repository creates default data using custom scaling group spec
        custom_spec = FairShareScalingGroupSpec(
            default_weight=Decimal("3.5"),
            half_life_days=10,
            lookback_days=90,
            decay_unit_days=3,
            resource_weights=ResourceSlot({"cpu": Decimal("2.0"), "mem": Decimal("1.5")}),
        )

        default_data = DomainFairShareData(
            resource_group="default",
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=custom_spec.default_weight,
                    half_life_days=custom_spec.half_life_days,
                    lookback_days=custom_spec.lookback_days,
                    decay_unit_days=custom_spec.decay_unit_days,
                    resource_weights=custom_spec.resource_weights,
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=[
                        SlotQuantity("cpu", Decimal("0.0")),
                        SlotQuantity("mem", Decimal("0.0")),
                    ],
                    normalized_usage=Decimal("0.0"),
                    lookback_start=today,
                    lookback_end=today,
                    last_calculated_at=now,
                ),
                metadata=None,
                use_default=True,
            ),
        )
        mock_repository.get_domain_fair_share = AsyncMock(return_value=default_data)

        action = GetDomainFairShareAction(
            resource_group="default",
            domain_name="test-domain",
        )

        result = await service.get_domain_fair_share(action)

        # Verify default uses custom scaling group spec values
        assert result.data.data.spec.half_life_days == 10
        assert result.data.data.spec.lookback_days == 90
        assert result.data.data.spec.decay_unit_days == 3
        assert result.data.data.spec.resource_weights == ResourceSlot({
            "cpu": Decimal("2.0"),
            "mem": Decimal("1.5"),
        })
        assert result.data.data.spec.weight == Decimal("3.5")


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

    @pytest.mark.asyncio
    async def test_get_project_fair_share_returns_default_when_not_found_but_exists(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """When record not found but project exists, repository returns default values."""
        project_id = uuid.uuid4()
        now = datetime.now(UTC)
        today = now.date()
        # Repository now creates and returns complete default data internally
        default_data = ProjectFairShareData(
            resource_group="default",
            project_id=project_id,
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("2.0"),
                    half_life_days=7,
                    lookback_days=60,
                    decay_unit_days=2,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.5")}),
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=[
                        SlotQuantity("cpu", Decimal("0.0")),
                        SlotQuantity("mem", Decimal("0.0")),
                    ],
                    normalized_usage=Decimal("0.0"),
                    lookback_start=today,
                    lookback_end=today,
                    last_calculated_at=now,
                ),
                metadata=None,
                use_default=True,
            ),
        )
        mock_repository.get_project_fair_share = AsyncMock(return_value=default_data)

        action = GetProjectFairShareAction(
            resource_group="default",
            project_id=project_id,
        )

        result = await service.get_project_fair_share(action)

        # Service should just return the result from repository
        assert result.data == default_data
        assert result.data.data.spec.weight == Decimal("2.0")
        assert result.data.data.use_default is True
        assert result.data.domain_name == "test-domain"

    @pytest.mark.asyncio
    async def test_get_project_fair_share_raises_entity_not_found_when_entity_missing(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """When project doesn't exist, repository should raise ProjectNotFound."""
        project_id = uuid.uuid4()
        # Repository raises ProjectNotFound directly when project doesn't exist
        mock_repository.get_project_fair_share = AsyncMock(
            side_effect=ProjectNotFound(f"Project not found: {project_id}")
        )

        action = GetProjectFairShareAction(
            resource_group="default",
            project_id=project_id,
        )

        with pytest.raises(ProjectNotFound):
            await service.get_project_fair_share(action)

    @pytest.mark.asyncio
    async def test_get_project_fair_share_uses_scaling_group_spec_for_default(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Default values from repository should reflect custom scaling group spec settings."""
        project_id = uuid.uuid4()
        now = datetime.now(UTC)
        today = now.date()
        # Repository creates default data using custom scaling group spec
        custom_spec = FairShareScalingGroupSpec(
            default_weight=Decimal("3.5"),
            half_life_days=10,
            lookback_days=90,
            decay_unit_days=3,
            resource_weights=ResourceSlot({"cpu": Decimal("2.0"), "mem": Decimal("1.5")}),
        )

        default_data = ProjectFairShareData(
            resource_group="default",
            project_id=project_id,
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=custom_spec.default_weight,
                    half_life_days=custom_spec.half_life_days,
                    lookback_days=custom_spec.lookback_days,
                    decay_unit_days=custom_spec.decay_unit_days,
                    resource_weights=custom_spec.resource_weights,
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=[
                        SlotQuantity("cpu", Decimal("0.0")),
                        SlotQuantity("mem", Decimal("0.0")),
                    ],
                    normalized_usage=Decimal("0.0"),
                    lookback_start=today,
                    lookback_end=today,
                    last_calculated_at=now,
                ),
                metadata=None,
                use_default=True,
            ),
        )
        mock_repository.get_project_fair_share = AsyncMock(return_value=default_data)

        action = GetProjectFairShareAction(
            resource_group="default",
            project_id=project_id,
        )

        result = await service.get_project_fair_share(action)

        # Verify default uses custom scaling group spec values
        assert result.data.data.spec.half_life_days == 10
        assert result.data.data.spec.lookback_days == 90
        assert result.data.data.spec.decay_unit_days == 3
        assert result.data.data.spec.resource_weights == ResourceSlot({
            "cpu": Decimal("2.0"),
            "mem": Decimal("1.5"),
        })
        assert result.data.data.spec.weight == Decimal("3.5")


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

    @pytest.mark.asyncio
    async def test_get_user_fair_share_returns_default_when_not_found_but_exists(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """When record not found but user exists in project, repository returns default values."""
        project_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        now = datetime.now(UTC)
        today = now.date()
        # Repository now creates and returns complete default data internally
        default_data = UserFairShareData(
            resource_group="default",
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("2.0"),
                    half_life_days=7,
                    lookback_days=60,
                    decay_unit_days=2,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.5")}),
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=[
                        SlotQuantity("cpu", Decimal("0.0")),
                        SlotQuantity("mem", Decimal("0.0")),
                    ],
                    normalized_usage=Decimal("0.0"),
                    lookback_start=today,
                    lookback_end=today,
                    last_calculated_at=now,
                ),
                metadata=None,
                use_default=True,
            ),
            scheduling_rank=None,
        )
        mock_repository.get_user_fair_share = AsyncMock(return_value=default_data)

        action = GetUserFairShareAction(
            resource_group="default",
            project_id=project_id,
            user_uuid=user_uuid,
        )

        result = await service.get_user_fair_share(action)

        # Service should just return the result from repository
        assert result.data == default_data
        assert result.data.data.spec.weight == Decimal("2.0")
        assert result.data.data.use_default is True
        assert result.data.domain_name == "test-domain"
        assert result.data.scheduling_rank is None

    @pytest.mark.asyncio
    async def test_get_user_fair_share_raises_entity_not_found_when_entity_missing(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """When user doesn't exist in project, repository should raise UserNotFound."""
        project_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        # Repository raises UserNotFound directly when user doesn't exist in project
        mock_repository.get_user_fair_share = AsyncMock(
            side_effect=UserNotFound(f"User not found in project: {project_id}, {user_uuid}")
        )

        action = GetUserFairShareAction(
            resource_group="default",
            project_id=project_id,
            user_uuid=user_uuid,
        )

        with pytest.raises(UserNotFound):
            await service.get_user_fair_share(action)

    @pytest.mark.asyncio
    async def test_get_user_fair_share_uses_scaling_group_spec_for_default(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Default values from repository should reflect custom scaling group spec settings."""
        project_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        now = datetime.now(UTC)
        today = now.date()
        # Repository creates default data using custom scaling group spec
        custom_spec = FairShareScalingGroupSpec(
            default_weight=Decimal("3.5"),
            half_life_days=10,
            lookback_days=90,
            decay_unit_days=3,
            resource_weights=ResourceSlot({"cpu": Decimal("2.0"), "mem": Decimal("1.5")}),
        )

        default_data = UserFairShareData(
            resource_group="default",
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=custom_spec.default_weight,
                    half_life_days=custom_spec.half_life_days,
                    lookback_days=custom_spec.lookback_days,
                    decay_unit_days=custom_spec.decay_unit_days,
                    resource_weights=custom_spec.resource_weights,
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=Decimal("1.0"),
                    total_decayed_usage=[
                        SlotQuantity("cpu", Decimal("0.0")),
                        SlotQuantity("mem", Decimal("0.0")),
                    ],
                    normalized_usage=Decimal("0.0"),
                    lookback_start=today,
                    lookback_end=today,
                    last_calculated_at=now,
                ),
                metadata=None,
                use_default=True,
            ),
            scheduling_rank=None,
        )
        mock_repository.get_user_fair_share = AsyncMock(return_value=default_data)

        action = GetUserFairShareAction(
            resource_group="default",
            project_id=project_id,
            user_uuid=user_uuid,
        )

        result = await service.get_user_fair_share(action)

        # Verify default uses custom scaling group spec values
        assert result.data.data.spec.half_life_days == 10
        assert result.data.data.spec.lookback_days == 90
        assert result.data.data.spec.decay_unit_days == 3
        assert result.data.data.spec.resource_weights == ResourceSlot({
            "cpu": Decimal("2.0"),
            "mem": Decimal("1.5"),
        })
        assert result.data.data.spec.weight == Decimal("3.5")


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
        now = datetime.now(UTC)
        # Mock domain with record
        domain_with_record = DomainFairShareData(
            resource_group="default",
            domain_name="domain-with-record",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("2.0"),
                    half_life_days=14,
                    lookback_days=30,
                    decay_unit_days=1,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
                ),
                calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
                metadata=FairShareMetadata(created_at=now, updated_at=now),
                use_default=False,
            ),
        )

        # Mock default domain (without record in DB, created by Repository)
        domain_without_record = DomainFairShareData(
            resource_group="default",
            domain_name="domain-without-record",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("1.0"),
                    half_life_days=14,
                    lookback_days=30,
                    decay_unit_days=1,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
                ),
                calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
                metadata=None,
                use_default=True,
            ),
        )

        # Repository now returns Data objects directly
        entity_result = DomainFairShareEntitySearchResult(
            items=[domain_with_record, domain_without_record],
            total_count=2,
            has_next_page=False,
            has_previous_page=False,
        )

        mock_repository.search_rg_domain_fair_shares = AsyncMock(return_value=entity_result)

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

        # One with persisted record (use_default=False)
        assert any(item.data.use_default is False for item in result.items)
        # One with default (use_default=True)
        assert any(item.data.use_default is True for item in result.items)

    @pytest.mark.asyncio
    async def test_default_uses_scaling_group_default_weight(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Default values use scaling group's default_weight."""
        # Repository creates default with weight set to default_weight
        default_domain = DomainFairShareData(
            resource_group="default",
            domain_name="domain-without-record",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("1.0"),  # Repository sets default_weight here
                    half_life_days=14,
                    lookback_days=30,
                    decay_unit_days=1,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
                ),
                calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
                metadata=None,
                use_default=True,
            ),
        )

        entity_result = DomainFairShareEntitySearchResult(
            items=[default_domain],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

        mock_repository.search_rg_domain_fair_shares = AsyncMock(return_value=entity_result)

        scope = DomainFairShareSearchScope(resource_group="default")
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=0, limit=100),
            conditions=[],
            orders=[],
        )
        action = SearchRGDomainFairSharesAction(scope=scope, querier=querier)
        result = await service.search_rg_domain_fair_shares(action)

        # Domain without record has weight set to default_weight
        default = result.items[0]
        assert default.data.spec.weight == Decimal("1.0")
        assert default.data.use_default is True

    @pytest.mark.asyncio
    async def test_default_matches_scaling_group_spec(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Default values match scaling group settings."""
        # Custom scaling group spec
        custom_spec = FairShareScalingGroupSpec(
            default_weight=Decimal("2.5"),
            half_life_days=7,
            lookback_days=60,
            decay_unit_days=2,
            resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.5")}),
        )

        default_domain = DomainFairShareData(
            resource_group="default",
            domain_name="domain-without-record",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=custom_spec.default_weight,
                    half_life_days=custom_spec.half_life_days,
                    lookback_days=custom_spec.lookback_days,
                    decay_unit_days=custom_spec.decay_unit_days,
                    resource_weights=custom_spec.resource_weights,
                ),
                calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
                metadata=None,
                use_default=True,
            ),
        )

        entity_result = DomainFairShareEntitySearchResult(
            items=[default_domain],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

        mock_repository.search_rg_domain_fair_shares = AsyncMock(return_value=entity_result)

        scope = DomainFairShareSearchScope(resource_group="default")
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=0, limit=100),
            conditions=[],
            orders=[],
        )
        action = SearchRGDomainFairSharesAction(scope=scope, querier=querier)
        result = await service.search_rg_domain_fair_shares(action)

        default = result.items[0]
        # Verify defaults use scaling group spec
        assert default.data.spec.half_life_days == 7
        assert default.data.spec.lookback_days == 60
        assert default.data.spec.decay_unit_days == 2
        assert default.data.spec.resource_weights == ResourceSlot({
            "cpu": Decimal("1.0"),
            "mem": Decimal("0.5"),
        })
        assert default.data.spec.weight == Decimal("2.5")


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
        now = datetime.now(UTC)

        # Mock project with record
        project_with_record = ProjectFairShareData(
            resource_group="default",
            project_id=project_id_with_record,
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("2.0"),
                    half_life_days=14,
                    lookback_days=30,
                    decay_unit_days=1,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
                ),
                calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
                metadata=FairShareMetadata(created_at=now, updated_at=now),
                use_default=False,
            ),
        )

        # Mock default project
        project_without_record = ProjectFairShareData(
            resource_group="default",
            project_id=project_id_without_record,
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("1.0"),
                    half_life_days=14,
                    lookback_days=30,
                    decay_unit_days=1,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
                ),
                calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
                metadata=None,
                use_default=True,
            ),
        )

        # Repository returns Data objects directly
        entity_result = ProjectFairShareEntitySearchResult(
            items=[project_with_record, project_without_record],
            total_count=2,
            has_next_page=False,
            has_previous_page=False,
        )

        mock_repository.search_rg_project_fair_shares = AsyncMock(return_value=entity_result)

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
        assert any(item.data.use_default is False for item in result.items)
        assert any(item.data.use_default is True for item in result.items)


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
        now = datetime.now(UTC)

        # Mock user with record
        user_with_record = UserFairShareData(
            resource_group="default",
            user_uuid=user_uuid_with_record,
            project_id=project_id,
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("2.0"),
                    half_life_days=14,
                    lookback_days=30,
                    decay_unit_days=1,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
                ),
                calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
                metadata=FairShareMetadata(created_at=now, updated_at=now),
                use_default=False,
            ),
            scheduling_rank=None,
        )

        # Mock default user
        user_without_record = UserFairShareData(
            resource_group="default",
            user_uuid=user_uuid_without_record,
            project_id=project_id,
            domain_name="test-domain",
            data=FairShareData(
                spec=FairShareSpec(
                    weight=Decimal("1.0"),
                    half_life_days=14,
                    lookback_days=30,
                    decay_unit_days=1,
                    resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
                ),
                calculation_snapshot=MagicMock(spec=FairShareCalculationSnapshot),
                metadata=None,
                use_default=True,
            ),
            scheduling_rank=None,
        )

        # Repository returns Data objects directly
        entity_result = UserFairShareEntitySearchResult(
            items=[user_with_record, user_without_record],
            total_count=2,
            has_next_page=False,
            has_previous_page=False,
        )

        mock_repository.search_rg_user_fair_shares = AsyncMock(return_value=entity_result)

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
        assert any(item.data.use_default is False for item in result.items)
        assert any(item.data.use_default is True for item in result.items)
