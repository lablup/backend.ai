"""Tests for update_deployment_policy GQL mutation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
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

SAMPLE_DEPLOYMENT_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


# --- Test scenarios ---


@dataclass(frozen=True)
class StrategyConversionScenario:
    """Input → expected upserter output for a valid strategy conversion."""

    input: UpdateDeploymentPolicyInputGQL
    expected_spec: RollingUpdateSpec | BlueGreenSpec
    expected_rollback_on_failure: bool


@dataclass(frozen=True)
class MissingConfigScenario:
    """Input that should raise due to missing strategy config."""

    input: UpdateDeploymentPolicyInputGQL
    expected_error_match: str


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


@pytest.fixture
def mock_info(mock_upsert_processor: AsyncMock) -> MagicMock:
    """Create mock strawberry.Info with deployment processors."""
    info = MagicMock()
    info.context.processors.deployment.upsert_deployment_policy = mock_upsert_processor
    return info


@pytest.fixture
def rolling_update_input() -> UpdateDeploymentPolicyInputGQL:
    """Input for ROLLING strategy with custom surge/unavailable."""
    return UpdateDeploymentPolicyInputGQL(
        deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
        strategy=DeploymentStrategy.ROLLING,
        rollback_on_failure=True,
        rolling_update=RollingUpdateConfigInputGQL(max_surge=2, max_unavailable=1),
    )


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


class TestToUpserterConversion:
    """Tests for UpdateDeploymentPolicyInputGQL.to_upserter()."""

    @pytest.mark.parametrize(
        "scenario",
        [
            pytest.param(
                StrategyConversionScenario(
                    input=UpdateDeploymentPolicyInputGQL(
                        deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
                        strategy=DeploymentStrategy.ROLLING,
                        rollback_on_failure=True,
                        rolling_update=RollingUpdateConfigInputGQL(max_surge=2, max_unavailable=1),
                    ),
                    expected_spec=RollingUpdateSpec(max_surge=2, max_unavailable=1),
                    expected_rollback_on_failure=True,
                ),
                id="rolling",
            ),
            pytest.param(
                StrategyConversionScenario(
                    input=UpdateDeploymentPolicyInputGQL(
                        deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
                        strategy=DeploymentStrategy.BLUE_GREEN,
                        blue_green=BlueGreenConfigInputGQL(
                            auto_promote=True, promote_delay_seconds=30
                        ),
                    ),
                    expected_spec=BlueGreenSpec(auto_promote=True, promote_delay_seconds=30),
                    expected_rollback_on_failure=False,
                ),
                id="blue_green",
            ),
        ],
    )
    def test_converts_gql_input_to_upserter(self, scenario: StrategyConversionScenario) -> None:
        """Test that GQL input is correctly converted to DeploymentPolicyUpserter."""
        upserter = scenario.input.to_upserter()

        assert upserter.strategy == scenario.input.strategy
        assert upserter.strategy_spec == scenario.expected_spec
        assert upserter.rollback_on_failure is scenario.expected_rollback_on_failure

    @pytest.mark.parametrize(
        "scenario",
        [
            pytest.param(
                MissingConfigScenario(
                    input=UpdateDeploymentPolicyInputGQL(
                        deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
                        strategy=DeploymentStrategy.ROLLING,
                    ),
                    expected_error_match="rolling_update",
                ),
                id="rolling",
            ),
            pytest.param(
                MissingConfigScenario(
                    input=UpdateDeploymentPolicyInputGQL(
                        deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
                        strategy=DeploymentStrategy.BLUE_GREEN,
                    ),
                    expected_error_match="blue_green",
                ),
                id="blue_green",
            ),
        ],
    )
    def test_raises_when_strategy_config_is_missing(self, scenario: MissingConfigScenario) -> None:
        """Test that to_upserter() raises when matching strategy config is not provided."""
        with pytest.raises(InvalidAPIParameters, match=scenario.expected_error_match):
            scenario.input.to_upserter()

    def test_converts_deployment_id_to_uuid(self) -> None:
        """Test that string deployment_id is correctly parsed into UUID."""
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=RollingUpdateConfigInputGQL(),
        )
        upserter = input_gql.to_upserter()

        assert str(upserter.deployment_id) == SAMPLE_DEPLOYMENT_ID


# --- Resolver tests ---


class TestAdminUpdateDeploymentPolicyResolver:
    """Tests for update_deployment_policy resolver."""

    async def test_delegates_upsert_action_to_processor(
        self,
        mock_superadmin_user: MagicMock,
        mock_upsert_processor: AsyncMock,
        mock_info: MagicMock,
        rolling_update_input: UpdateDeploymentPolicyInputGQL,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that resolver delegates to processor and returns payload."""
        # Given
        policy_data = _make_policy_data(
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(max_surge=2, max_unavailable=1),
        )
        mock_upsert_processor.wait_for_complete.return_value = UpsertDeploymentPolicyActionResult(
            data=policy_data,
            created=True,
        )

        monkeypatch.setattr(
            gql_utils,
            "current_user",
            lambda: mock_superadmin_user,
        )

        # When
        resolver_fn = policy_resolver.update_deployment_policy.base_resolver
        result = await resolver_fn(rolling_update_input, mock_info)

        # Then
        mock_upsert_processor.wait_for_complete.assert_called_once()
        call_args = mock_upsert_processor.wait_for_complete.call_args
        action = call_args[0][0]

        assert str(action.upserter.deployment_id) == SAMPLE_DEPLOYMENT_ID
        assert action.upserter.strategy == DeploymentStrategy.ROLLING
        assert action.upserter.rollback_on_failure is True

        assert isinstance(result, UpdateDeploymentPolicyPayloadGQL)

    async def test_rejects_non_superadmin(
        self,
        mock_regular_user: MagicMock,
        mock_upsert_processor: AsyncMock,
        mock_info: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that non-superadmin user is rejected with HTTPForbidden."""
        # Given
        monkeypatch.setattr(
            gql_utils,
            "current_user",
            lambda: mock_regular_user,
        )

        input_data = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=RollingUpdateConfigInputGQL(),
        )

        # When / Then
        resolver_fn = policy_resolver.update_deployment_policy.base_resolver
        with pytest.raises(web.HTTPForbidden):
            await resolver_fn(input_data, mock_info)

        mock_upsert_processor.wait_for_complete.assert_not_called()
