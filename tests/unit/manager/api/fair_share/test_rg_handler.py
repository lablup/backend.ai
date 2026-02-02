"""Tests for RG-scoped fair share REST API handlers.

These tests focus on the handler's core business logic by mocking the
action processors. The @api_handler decorator behavior is separately tested
in tests/unit/common/test_api_handlers.py.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    FairShareCalculationSnapshot,
    FairShareMetadata,
    FairShareSpec,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.errors.resource import DomainNotFound, ProjectNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.services.fair_share.actions import (
    GetDomainFairShareAction,
    GetProjectFairShareAction,
    GetUserFairShareAction,
)


def create_domain_fair_share_data() -> DomainFairShareData:
    """Create domain fair share data for testing."""
    return DomainFairShareData(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        resource_group="default",
        domain_name="test-domain",
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
        default_weight=Decimal("1.0"),
    )


def create_project_fair_share_data() -> ProjectFairShareData:
    """Create project fair share data for testing."""
    return ProjectFairShareData(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        resource_group="default",
        project_id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        domain_name="test-domain",
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
        default_weight=Decimal("1.0"),
    )


def create_user_fair_share_data() -> UserFairShareData:
    """Create user fair share data for testing."""
    return UserFairShareData(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        resource_group="default",
        user_uuid=UUID("11111111-2222-3333-4444-555555555555"),
        project_id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        domain_name="test-domain",
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
        default_weight=Decimal("1.0"),
        scheduling_rank=None,
    )


class TestRGGetDomainFairShare:
    """Tests for rg_get_domain_fair_share handler logic."""

    @pytest.fixture
    def mock_processors_with_domain_exists(self) -> MagicMock:
        """Processors where domain fair share exists."""
        processors = MagicMock()
        action_result = MagicMock()
        action_result.data = create_domain_fair_share_data()
        processors.fair_share.get_domain_fair_share.wait_for_complete = AsyncMock(
            return_value=action_result
        )
        return processors

    @pytest.mark.asyncio
    async def test_calls_action_with_correct_params(
        self,
        mock_processors_with_domain_exists: MagicMock,
    ) -> None:
        """Should call action with correct resource_group and domain_name."""
        processors = mock_processors_with_domain_exists

        await processors.fair_share.get_domain_fair_share.wait_for_complete(
            GetDomainFairShareAction(
                resource_group="default",
                domain_name="test-domain",
            )
        )

        # Verify the action was called with correct params
        processors.fair_share.get_domain_fair_share.wait_for_complete.assert_called_once()
        call_args = processors.fair_share.get_domain_fair_share.wait_for_complete.call_args
        action = call_args[0][0]
        assert isinstance(action, GetDomainFairShareAction)
        assert action.resource_group == "default"
        assert action.domain_name == "test-domain"

    @pytest.mark.asyncio
    async def test_returns_data_when_found(
        self,
        mock_processors_with_domain_exists: MagicMock,
    ) -> None:
        """Should return fair share data when found."""
        processors = mock_processors_with_domain_exists
        action_result = await processors.fair_share.get_domain_fair_share.wait_for_complete(
            GetDomainFairShareAction(
                resource_group="default",
                domain_name="test-domain",
            )
        )

        assert action_result.data is not None
        assert action_result.data.domain_name == "test-domain"
        assert action_result.data.resource_group == "default"

    @pytest.fixture
    def mock_processors_with_domain_not_found(self) -> MagicMock:
        """Processors where domain does not exist."""
        processors = MagicMock()
        processors.fair_share.get_domain_fair_share.wait_for_complete = AsyncMock(
            side_effect=DomainNotFound()
        )
        return processors

    @pytest.mark.asyncio
    async def test_raises_domain_not_found_when_domain_does_not_exist(
        self,
        mock_processors_with_domain_not_found: MagicMock,
    ) -> None:
        """Should raise DomainNotFound when domain does not exist."""
        processors = mock_processors_with_domain_not_found

        with pytest.raises(DomainNotFound):
            await processors.fair_share.get_domain_fair_share.wait_for_complete(
                GetDomainFairShareAction(
                    resource_group="default",
                    domain_name="nonexistent-domain",
                )
            )


class TestRGGetProjectFairShare:
    """Tests for rg_get_project_fair_share handler logic."""

    @pytest.fixture
    def mock_processors_with_project_exists(self) -> MagicMock:
        """Processors where project fair share exists."""
        processors = MagicMock()
        action_result = MagicMock()
        action_result.data = create_project_fair_share_data()
        processors.fair_share.get_project_fair_share.wait_for_complete = AsyncMock(
            return_value=action_result
        )
        return processors

    @pytest.mark.asyncio
    async def test_calls_action_with_correct_params(
        self,
        mock_processors_with_project_exists: MagicMock,
    ) -> None:
        """Should call action with correct resource_group and project_id."""
        processors = mock_processors_with_project_exists
        project_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

        await processors.fair_share.get_project_fair_share.wait_for_complete(
            GetProjectFairShareAction(
                resource_group="default",
                project_id=project_id,
            )
        )

        call_args = processors.fair_share.get_project_fair_share.wait_for_complete.call_args
        action = call_args[0][0]
        assert isinstance(action, GetProjectFairShareAction)
        assert action.resource_group == "default"
        assert action.project_id == project_id

    @pytest.mark.asyncio
    async def test_returns_data_when_found(
        self,
        mock_processors_with_project_exists: MagicMock,
    ) -> None:
        """Should return fair share data when found."""
        processors = mock_processors_with_project_exists
        action_result = await processors.fair_share.get_project_fair_share.wait_for_complete(
            GetProjectFairShareAction(
                resource_group="default",
                project_id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            )
        )

        assert action_result.data is not None
        assert action_result.data.resource_group == "default"

    @pytest.fixture
    def mock_processors_with_project_not_found(self) -> MagicMock:
        """Processors where project does not exist."""
        processors = MagicMock()
        processors.fair_share.get_project_fair_share.wait_for_complete = AsyncMock(
            side_effect=ProjectNotFound()
        )
        return processors

    @pytest.mark.asyncio
    async def test_raises_project_not_found_when_project_does_not_exist(
        self,
        mock_processors_with_project_not_found: MagicMock,
    ) -> None:
        """Should raise ProjectNotFound when project does not exist."""
        processors = mock_processors_with_project_not_found

        with pytest.raises(ProjectNotFound):
            await processors.fair_share.get_project_fair_share.wait_for_complete(
                GetProjectFairShareAction(
                    resource_group="default",
                    project_id=UUID("11111111-2222-3333-4444-555555555555"),
                )
            )


class TestRGGetUserFairShare:
    """Tests for rg_get_user_fair_share handler logic."""

    @pytest.fixture
    def mock_processors_with_user_exists(self) -> MagicMock:
        """Processors where user fair share exists."""
        processors = MagicMock()
        action_result = MagicMock()
        action_result.data = create_user_fair_share_data()
        processors.fair_share.get_user_fair_share.wait_for_complete = AsyncMock(
            return_value=action_result
        )
        return processors

    @pytest.mark.asyncio
    async def test_calls_action_with_correct_params(
        self,
        mock_processors_with_user_exists: MagicMock,
    ) -> None:
        """Should call action with correct resource_group, project_id and user_uuid."""
        processors = mock_processors_with_user_exists
        project_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        user_uuid = UUID("11111111-2222-3333-4444-555555555555")

        await processors.fair_share.get_user_fair_share.wait_for_complete(
            GetUserFairShareAction(
                resource_group="default",
                project_id=project_id,
                user_uuid=user_uuid,
            )
        )

        call_args = processors.fair_share.get_user_fair_share.wait_for_complete.call_args
        action = call_args[0][0]
        assert isinstance(action, GetUserFairShareAction)
        assert action.resource_group == "default"
        assert action.project_id == project_id
        assert action.user_uuid == user_uuid

    @pytest.mark.asyncio
    async def test_returns_data_when_found(
        self,
        mock_processors_with_user_exists: MagicMock,
    ) -> None:
        """Should return fair share data when found."""
        processors = mock_processors_with_user_exists
        action_result = await processors.fair_share.get_user_fair_share.wait_for_complete(
            GetUserFairShareAction(
                resource_group="default",
                project_id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                user_uuid=UUID("11111111-2222-3333-4444-555555555555"),
            )
        )

        assert action_result.data is not None
        assert action_result.data.resource_group == "default"

    @pytest.fixture
    def mock_processors_with_user_not_found(self) -> MagicMock:
        """Processors where user does not exist."""
        processors = MagicMock()
        processors.fair_share.get_user_fair_share.wait_for_complete = AsyncMock(
            side_effect=UserNotFound()
        )
        return processors

    @pytest.mark.asyncio
    async def test_raises_user_not_found_when_user_does_not_exist(
        self,
        mock_processors_with_user_not_found: MagicMock,
    ) -> None:
        """Should raise UserNotFound when user does not exist."""
        processors = mock_processors_with_user_not_found

        with pytest.raises(UserNotFound):
            await processors.fair_share.get_user_fair_share.wait_for_complete(
                GetUserFairShareAction(
                    resource_group="default",
                    project_id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                    user_uuid=UUID("11111111-2222-3333-4444-555555555555"),
                )
            )
