"""Tests for admin_update_deployment_policy GQL mutation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from strawberry import ID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.api.gql import utils as gql_utils
from ai.backend.manager.api.gql.deployment.resolver import policy as policy_resolver
from ai.backend.manager.api.gql.deployment.types.policy import (
    BlueGreenConfigInputGQL,
    RollingUpdateConfigInputGQL,
    UpdateDeploymentPolicyInputGQL,
    UpdateDeploymentPolicyPayloadGQL,
)
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.services.deployment.actions.deployment_policy.upsert_deployment_policy import (
    UpsertDeploymentPolicyActionResult,
)

# --- Fixtures ---


@pytest.fixture
def mock_superadmin_user() -> MagicMock:
    """Create mock superadmin user."""
    user = MagicMock()
    user.is_superadmin = True
    return user


@pytest.fixture
def mock_regular_user() -> MagicMock:
    """Create mock regular (non-superadmin) user."""
    user = MagicMock()
    user.is_superadmin = False
    return user


@pytest.fixture
def mock_upsert_processor() -> AsyncMock:
    """Create mock upsert_deployment_policy processor."""
    return AsyncMock()


def _create_mock_info(processor: AsyncMock) -> MagicMock:
    """Create mock strawberry.Info with deployment processors."""
    info = MagicMock()
    info.context.processors.deployment.upsert_deployment_policy = processor
    return info


def _make_policy_data(
    *,
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING,
    strategy_spec: RollingUpdateSpec | BlueGreenSpec | None = None,
) -> DeploymentPolicyData:
    """Create a DeploymentPolicyData for mock results."""
    if strategy_spec is None:
        strategy_spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
    return DeploymentPolicyData(
        id=uuid.uuid4(),
        endpoint=uuid.uuid4(),
        strategy=strategy,
        strategy_spec=strategy_spec,
        rollback_on_failure=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


# --- Input type conversion tests ---


class TestUpdateDeploymentPolicyInputGQL:
    """Tests for UpdateDeploymentPolicyInputGQL.to_upserter()."""

    def test_rolling_strategy_with_config(self) -> None:
        """Test conversion with ROLLING strategy and config provided."""
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.ROLLING,
            rollback_on_failure=True,
            rolling_update=RollingUpdateConfigInputGQL(max_surge=2, max_unavailable=1),
        )
        upserter = input_gql.to_upserter()

        assert upserter.strategy == DeploymentStrategy.ROLLING
        assert isinstance(upserter.strategy_spec, RollingUpdateSpec)
        assert upserter.strategy_spec.max_surge == 2
        assert upserter.strategy_spec.max_unavailable == 1
        assert upserter.rollback_on_failure is True

    def test_blue_green_strategy_with_config(self) -> None:
        """Test conversion with BLUE_GREEN strategy and config provided."""
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.BLUE_GREEN,
            blue_green=BlueGreenConfigInputGQL(auto_promote=True, promote_delay_seconds=30),
        )
        upserter = input_gql.to_upserter()

        assert upserter.strategy == DeploymentStrategy.BLUE_GREEN
        assert isinstance(upserter.strategy_spec, BlueGreenSpec)
        assert upserter.strategy_spec.auto_promote is True
        assert upserter.strategy_spec.promote_delay_seconds == 30
        assert upserter.rollback_on_failure is False

    def test_rolling_strategy_missing_config_raises(self) -> None:
        """Test that ROLLING strategy without rolling_update config raises."""
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.ROLLING,
        )
        with pytest.raises(InvalidAPIParameters, match="rolling_update"):
            input_gql.to_upserter()

    def test_blue_green_strategy_missing_config_raises(self) -> None:
        """Test that BLUE_GREEN strategy without blue_green config raises."""
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.BLUE_GREEN,
        )
        with pytest.raises(InvalidAPIParameters, match="blue_green"):
            input_gql.to_upserter()

    def test_deployment_id_is_converted_to_uuid(self) -> None:
        """Test that deployment_id string is correctly converted to UUID."""
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=RollingUpdateConfigInputGQL(),
        )
        upserter = input_gql.to_upserter()

        assert str(upserter.deployment_id) == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


# --- Resolver tests ---


class TestAdminUpdateDeploymentPolicyMutation:
    """Tests for admin_update_deployment_policy resolver."""

    async def test_mutation_calls_processor_with_correct_action(
        self,
        mock_superadmin_user: MagicMock,
        mock_upsert_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation calls processor with correct action parameters."""
        # Given
        policy_data = _make_policy_data(
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(max_surge=2, max_unavailable=1),
        )
        mock_upsert_processor.wait_for_complete.return_value = UpsertDeploymentPolicyActionResult(
            data=policy_data,
            created=True,
        )
        mock_info = _create_mock_info(mock_upsert_processor)

        monkeypatch.setattr(
            gql_utils,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.ROLLING,
            rollback_on_failure=True,
            rolling_update=RollingUpdateConfigInputGQL(max_surge=2, max_unavailable=1),
        )

        # When
        resolver_fn = policy_resolver.admin_update_deployment_policy.base_resolver
        result = await resolver_fn(input_data, mock_info)

        # Then
        mock_upsert_processor.wait_for_complete.assert_called_once()
        call_args = mock_upsert_processor.wait_for_complete.call_args
        action = call_args[0][0]

        assert str(action.upserter.deployment_id) == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        assert action.upserter.strategy == DeploymentStrategy.ROLLING
        assert action.upserter.rollback_on_failure is True

        assert isinstance(result, UpdateDeploymentPolicyPayloadGQL)
        assert result.created is True

    async def test_mutation_returns_created_false_on_update(
        self,
        mock_superadmin_user: MagicMock,
        mock_upsert_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation returns created=False when policy already exists."""
        # Given
        policy_data = _make_policy_data()
        mock_upsert_processor.wait_for_complete.return_value = UpsertDeploymentPolicyActionResult(
            data=policy_data,
            created=False,
        )
        mock_info = _create_mock_info(mock_upsert_processor)

        monkeypatch.setattr(
            gql_utils,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=RollingUpdateConfigInputGQL(),
        )

        # When
        resolver_fn = policy_resolver.admin_update_deployment_policy.base_resolver
        result = await resolver_fn(input_data, mock_info)

        # Then
        assert result.created is False

    async def test_mutation_requires_superadmin(
        self,
        mock_regular_user: MagicMock,
        mock_upsert_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation requires superadmin privilege."""
        # Given
        mock_info = _create_mock_info(mock_upsert_processor)

        monkeypatch.setattr(
            gql_utils,
            "current_user",
            lambda: mock_regular_user,
        )

        input_data = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=RollingUpdateConfigInputGQL(),
        )

        # When / Then
        resolver_fn = policy_resolver.admin_update_deployment_policy.base_resolver
        with pytest.raises(web.HTTPForbidden):
            await resolver_fn(input_data, mock_info)

        mock_upsert_processor.wait_for_complete.assert_not_called()
