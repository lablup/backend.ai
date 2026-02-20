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
from ai.backend.manager.data.deployment.types import DeploymentPolicySearchResult
from ai.backend.manager.models.deployment_policy import (
    DeploymentPolicyData,
    RollingUpdateSpec,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.services.deployment.actions.deployment_policy import (
    SearchDeploymentPoliciesAction,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.sokovan.deployment import DeploymentController


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
