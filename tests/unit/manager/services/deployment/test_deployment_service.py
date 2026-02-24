"""
Mock-based unit tests for DeploymentService deployment policy operations.

Tests verify service layer business logic using mocked repositories.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment.creator import DeploymentPolicyConfig
from ai.backend.manager.data.deployment.types import (
    DeploymentPolicyData,
    DeploymentPolicySearchResult,
)
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.updaters import DeploymentPolicyUpdaterSpec
from ai.backend.manager.services.deployment.actions.deployment_policy import (
    CreateDeploymentPolicyAction,
    SearchDeploymentPoliciesAction,
    UpdateDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.sokovan.deployment import DeploymentController
from ai.backend.manager.types import OptionalState


class DeploymentServiceBaseFixtures:
    """Base class containing shared fixtures for deployment service tests."""

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        """Mock DeploymentRepository for testing."""
        return MagicMock(spec=DeploymentRepository)

    @pytest.fixture
    def mock_deployment_controller(self) -> MagicMock:
        """Mock DeploymentController for testing."""
        return MagicMock(spec=DeploymentController)

    @pytest.fixture
    def deployment_service(
        self,
        mock_deployment_controller: MagicMock,
        mock_deployment_repository: MagicMock,
    ) -> DeploymentService:
        """Create DeploymentService with mock dependencies."""
        return DeploymentService(
            deployment_controller=mock_deployment_controller,
            deployment_repository=mock_deployment_repository,
        )

    @pytest.fixture
    def processors(self, deployment_service: DeploymentService) -> DeploymentProcessors:
        """Create DeploymentProcessors with mock DeploymentService."""
        return DeploymentProcessors(deployment_service, [])

    @pytest.fixture
    def deployment_policy_data(self) -> DeploymentPolicyData:
        """Sample deployment policy data for testing."""
        return DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=uuid.uuid4(),
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(max_surge=1, max_unavailable=0),
            rollback_on_failure=False,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )


class TestSearchDeploymentPolicies(DeploymentServiceBaseFixtures):
    """Tests for DeploymentService.search_deployment_policies"""

    async def test_search_deployment_policies_success(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
    ) -> None:
        """Search deployment policies should return matching results."""
        mock_deployment_repository.search_deployment_policies = AsyncMock(
            return_value=DeploymentPolicySearchResult(
                items=[deployment_policy_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchDeploymentPoliciesAction(querier=querier)

        result = await processors.search_deployment_policies.wait_for_complete(action)

        assert result.data == [deployment_policy_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_deployment_repository.search_deployment_policies.assert_called_once_with(querier)

    async def test_search_deployment_policies_empty_result(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
    ) -> None:
        """Search deployment policies should return empty list when no results found."""
        mock_deployment_repository.search_deployment_policies = AsyncMock(
            return_value=DeploymentPolicySearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchDeploymentPoliciesAction(querier=querier)

        result = await processors.search_deployment_policies.wait_for_complete(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_deployment_policies_with_pagination(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
    ) -> None:
        """Search deployment policies should handle pagination correctly."""
        mock_deployment_repository.search_deployment_policies = AsyncMock(
            return_value=DeploymentPolicySearchResult(
                items=[deployment_policy_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchDeploymentPoliciesAction(querier=querier)

        result = await processors.search_deployment_policies.wait_for_complete(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True


class TestCreateDeploymentPolicy(DeploymentServiceBaseFixtures):
    """Tests for DeploymentService.create_deployment_policy"""

    @pytest.fixture
    def rolling_policy_config(self) -> DeploymentPolicyConfig:
        """Policy config for rolling update strategy."""
        return DeploymentPolicyConfig(
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(max_surge=1, max_unavailable=0),
            rollback_on_failure=False,
        )

    @pytest.fixture
    def blue_green_policy_config(self) -> DeploymentPolicyConfig:
        """Policy config for blue-green strategy."""
        return DeploymentPolicyConfig(
            strategy=DeploymentStrategy.BLUE_GREEN,
            strategy_spec=BlueGreenSpec(auto_promote=True, promote_delay_seconds=30),
            rollback_on_failure=True,
        )

    @pytest.fixture
    def blue_green_deployment_policy_data(
        self,
        blue_green_policy_config: DeploymentPolicyConfig,
    ) -> DeploymentPolicyData:
        """Sample blue-green deployment policy data for testing."""
        return DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=uuid.uuid4(),
            strategy=blue_green_policy_config.strategy,
            strategy_spec=blue_green_policy_config.strategy_spec,
            rollback_on_failure=blue_green_policy_config.rollback_on_failure,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )

    async def test_create_deployment_policy_success(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        rolling_policy_config: DeploymentPolicyConfig,
    ) -> None:
        """Create deployment policy should return the created policy data."""
        mock_deployment_repository.create_deployment_policy = AsyncMock(
            return_value=deployment_policy_data,
        )

        action = CreateDeploymentPolicyAction(
            endpoint_id=deployment_policy_data.endpoint,
            policy_config=rolling_policy_config,
        )

        result = await processors.create_deployment_policy.wait_for_complete(action)

        assert result.data == deployment_policy_data
        assert result.entity_id() == str(deployment_policy_data.id)
        mock_deployment_repository.create_deployment_policy.assert_called_once()

    async def test_create_deployment_policy_blue_green(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        blue_green_deployment_policy_data: DeploymentPolicyData,
        blue_green_policy_config: DeploymentPolicyConfig,
    ) -> None:
        """Create deployment policy with BLUE_GREEN strategy."""
        mock_deployment_repository.create_deployment_policy = AsyncMock(
            return_value=blue_green_deployment_policy_data,
        )

        action = CreateDeploymentPolicyAction(
            endpoint_id=blue_green_deployment_policy_data.endpoint,
            policy_config=blue_green_policy_config,
        )

        result = await processors.create_deployment_policy.wait_for_complete(action)

        assert result.data == blue_green_deployment_policy_data
        assert result.data.strategy == DeploymentStrategy.BLUE_GREEN
        assert result.data.rollback_on_failure is True


class TestUpdateDeploymentPolicy(DeploymentServiceBaseFixtures):
    """Tests for DeploymentService.update_deployment_policy"""

    @pytest.fixture
    def full_updater_spec(self) -> DeploymentPolicyUpdaterSpec:
        """Updater spec that changes both strategy and strategy_spec."""
        return DeploymentPolicyUpdaterSpec(
            strategy=OptionalState[DeploymentStrategy].update(DeploymentStrategy.ROLLING),
            strategy_spec=OptionalState[RollingUpdateSpec | BlueGreenSpec].update(
                RollingUpdateSpec(max_surge=2, max_unavailable=1)
            ),
        )

    @pytest.fixture
    def partial_updater_spec(self) -> DeploymentPolicyUpdaterSpec:
        """Updater spec that only changes rollback_on_failure."""
        return DeploymentPolicyUpdaterSpec(
            rollback_on_failure=OptionalState[bool].update(True),
        )

    @pytest.fixture
    def partially_updated_policy_data(self) -> DeploymentPolicyData:
        """Policy data reflecting a partial update (rollback_on_failure changed)."""
        return DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=uuid.uuid4(),
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(max_surge=1, max_unavailable=0),
            rollback_on_failure=True,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 6, 1, 0, 0, 0, tzinfo=UTC),
        )

    async def test_update_deployment_policy_success(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        full_updater_spec: DeploymentPolicyUpdaterSpec,
    ) -> None:
        """Update deployment policy should return the updated policy data."""
        mock_deployment_repository.update_deployment_policy = AsyncMock(
            return_value=deployment_policy_data,
        )

        action = UpdateDeploymentPolicyAction(
            policy_id=deployment_policy_data.id,
            updater_spec=full_updater_spec,
        )

        result = await processors.update_deployment_policy.wait_for_complete(action)

        assert result.data == deployment_policy_data
        assert result.entity_id() == str(deployment_policy_data.id)
        mock_deployment_repository.update_deployment_policy.assert_called_once()

    async def test_update_deployment_policy_partial(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        partially_updated_policy_data: DeploymentPolicyData,
        partial_updater_spec: DeploymentPolicyUpdaterSpec,
    ) -> None:
        """Update deployment policy with partial update (only rollback_on_failure)."""
        mock_deployment_repository.update_deployment_policy = AsyncMock(
            return_value=partially_updated_policy_data,
        )

        action = UpdateDeploymentPolicyAction(
            policy_id=partially_updated_policy_data.id,
            updater_spec=partial_updater_spec,
        )

        result = await processors.update_deployment_policy.wait_for_complete(action)

        assert result.data == partially_updated_policy_data
        assert result.data.rollback_on_failure is True
        mock_deployment_repository.update_deployment_policy.assert_called_once()
