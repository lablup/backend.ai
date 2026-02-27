"""
Mock-based unit tests for DeploymentService.search_deployment_policies.

Tests verify service layer business logic using mocked repositories.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment.types import (
    DeploymentPolicyData,
    DeploymentPolicySearchResult,
)
from ai.backend.manager.models.deployment_policy import (
    BlueGreenSpec,
    DeploymentPolicyRow,
    RollingUpdateSpec,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator, OffsetPagination
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators.policy import (
    DeploymentPolicyCreatorSpec,
)
from ai.backend.manager.repositories.deployment.updaters import DeploymentPolicyUpdaterSpec
from ai.backend.manager.services.deployment.actions.deployment_policy import (
    SearchDeploymentPoliciesAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.create_deployment_policy import (
    CreateDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy.update_deployment_policy import (
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

    @pytest.fixture
    def endpoint_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def policy_id(self) -> uuid.UUID:
        return uuid.uuid4()


class TestSearchDeploymentPolicies(DeploymentServiceBaseFixtures):
    """Tests for DeploymentService.search_deployment_policies"""

    @pytest.fixture
    def default_querier(self) -> BatchQuerier:
        return BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

    @pytest.fixture
    def paginated_querier(self) -> BatchQuerier:
        return BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

    async def test_search_deployment_policies_success(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        default_querier: BatchQuerier,
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

        action = SearchDeploymentPoliciesAction(querier=default_querier)

        result = await processors.search_deployment_policies.wait_for_complete(action)

        assert result.data == [deployment_policy_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_deployment_repository.search_deployment_policies.assert_called_once_with(
            default_querier
        )

    async def test_search_deployment_policies_empty_result(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        default_querier: BatchQuerier,
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

        action = SearchDeploymentPoliciesAction(querier=default_querier)

        result = await processors.search_deployment_policies.wait_for_complete(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_deployment_policies_with_pagination(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        paginated_querier: BatchQuerier,
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

        action = SearchDeploymentPoliciesAction(querier=paginated_querier)

        result = await processors.search_deployment_policies.wait_for_complete(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True


class TestCreateDeploymentPolicy(DeploymentServiceBaseFixtures):
    """Tests for DeploymentService.create_deployment_policy"""

    @pytest.fixture
    def rolling_creator_spec(self, endpoint_id: uuid.UUID) -> DeploymentPolicyCreatorSpec:
        return DeploymentPolicyCreatorSpec(
            endpoint_id=endpoint_id,
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(max_surge=2, max_unavailable=1),
            rollback_on_failure=True,
        )

    @pytest.fixture
    def blue_green_creator_spec(self, endpoint_id: uuid.UUID) -> DeploymentPolicyCreatorSpec:
        return DeploymentPolicyCreatorSpec(
            endpoint_id=endpoint_id,
            strategy=DeploymentStrategy.BLUE_GREEN,
            strategy_spec=BlueGreenSpec(auto_promote=True, promote_delay_seconds=30),
            rollback_on_failure=False,
        )

    @pytest.fixture
    def blue_green_policy_data(self) -> DeploymentPolicyData:
        return DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=uuid.uuid4(),
            strategy=DeploymentStrategy.BLUE_GREEN,
            strategy_spec=BlueGreenSpec(auto_promote=True, promote_delay_seconds=30),
            rollback_on_failure=False,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )

    async def test_create_deployment_policy_rolling(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        endpoint_id: uuid.UUID,
        rolling_creator_spec: DeploymentPolicyCreatorSpec,
    ) -> None:
        """Create deployment policy with ROLLING strategy should succeed."""
        mock_deployment_repository.create_deployment_policy = AsyncMock(
            return_value=deployment_policy_data
        )

        creator = Creator[DeploymentPolicyRow](spec=rolling_creator_spec)
        action = CreateDeploymentPolicyAction(creator=creator)

        result = await processors.create_deployment_policy.wait_for_complete(action)

        assert result.data == deployment_policy_data
        mock_deployment_repository.create_deployment_policy.assert_called_once()
        creator_arg = mock_deployment_repository.create_deployment_policy.call_args[0][0]
        spec = creator_arg.spec
        assert spec.endpoint_id == endpoint_id
        assert spec.strategy == DeploymentStrategy.ROLLING
        assert spec.rollback_on_failure is True

    async def test_create_deployment_policy_blue_green(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        blue_green_creator_spec: DeploymentPolicyCreatorSpec,
        blue_green_policy_data: DeploymentPolicyData,
    ) -> None:
        """Create deployment policy with BLUE_GREEN strategy should succeed."""
        mock_deployment_repository.create_deployment_policy = AsyncMock(
            return_value=blue_green_policy_data
        )

        creator = Creator[DeploymentPolicyRow](spec=blue_green_creator_spec)
        action = CreateDeploymentPolicyAction(creator=creator)

        result = await processors.create_deployment_policy.wait_for_complete(action)

        assert result.data == blue_green_policy_data
        assert result.data.strategy == DeploymentStrategy.BLUE_GREEN


class TestUpdateDeploymentPolicy(DeploymentServiceBaseFixtures):
    """Tests for DeploymentService.update_deployment_policy"""

    @pytest.fixture
    def full_update_action(self, policy_id: uuid.UUID) -> UpdateDeploymentPolicyAction:
        updater_spec = DeploymentPolicyUpdaterSpec(
            strategy=OptionalState.update(DeploymentStrategy.ROLLING),
            rollback_on_failure=OptionalState.update(True),
        )
        updater: Updater[DeploymentPolicyRow] = Updater(
            spec=updater_spec,
            pk_value=policy_id,
        )
        return UpdateDeploymentPolicyAction(
            policy_id=policy_id,
            updater=updater,
        )

    @pytest.fixture
    def partial_update_action(self, policy_id: uuid.UUID) -> UpdateDeploymentPolicyAction:
        updater_spec = DeploymentPolicyUpdaterSpec(
            rollback_on_failure=OptionalState.update(False),
        )
        updater: Updater[DeploymentPolicyRow] = Updater(
            spec=updater_spec,
            pk_value=policy_id,
        )
        return UpdateDeploymentPolicyAction(
            policy_id=policy_id,
            updater=updater,
        )

    async def test_update_deployment_policy_success(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        full_update_action: UpdateDeploymentPolicyAction,
    ) -> None:
        """Update deployment policy should succeed."""
        mock_deployment_repository.update_deployment_policy = AsyncMock(
            return_value=deployment_policy_data
        )

        result = await processors.update_deployment_policy.wait_for_complete(full_update_action)

        assert result.data == deployment_policy_data
        mock_deployment_repository.update_deployment_policy.assert_called_once_with(
            full_update_action.updater
        )

    async def test_update_deployment_policy_partial_update(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        partial_update_action: UpdateDeploymentPolicyAction,
    ) -> None:
        """Update deployment policy with partial fields should succeed."""
        mock_deployment_repository.update_deployment_policy = AsyncMock(
            return_value=deployment_policy_data
        )

        result = await processors.update_deployment_policy.wait_for_complete(partial_update_action)

        assert result.data == deployment_policy_data
        mock_deployment_repository.update_deployment_policy.assert_called_once()
