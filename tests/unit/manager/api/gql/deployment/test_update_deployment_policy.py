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
from ai.backend.common.dto.manager.v2.deployment.request import (
    BlueGreenConfigInput,
    RollingUpdateConfigInput,
    UpsertDeploymentPolicyInput,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    DeploymentPolicyNode as DeploymentPolicyNodeDTO,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    UpsertDeploymentPolicyPayload as UpsertDeploymentPolicyPayloadDTO,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    BlueGreenConfigInfo,
    BlueGreenStrategySpecInfo,
    IntOrPercent,
    RollingUpdateConfigInfo,
    RollingUpdateStrategySpecInfo,
)
from ai.backend.manager.api.gql import utils as gql_utils
from ai.backend.manager.api.gql.deployment.resolver import policy as policy_resolver
from ai.backend.manager.api.gql.deployment.types.policy import (
    BlueGreenConfigInputGQL,
    IntOrPercentInputGQL,
    RollingUpdateConfigInputGQL,
    UpdateDeploymentPolicyInputGQL,
    UpdateDeploymentPolicyPayloadGQL,
)

SAMPLE_DEPLOYMENT_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _int_or_percent(value: int | float) -> IntOrPercent:
    """Build an IntOrPercent from a plain int or float for test brevity."""
    if isinstance(value, float):
        return IntOrPercent(percent=value)
    return IntOrPercent(count=value)


# --- Test scenarios ---


@dataclass(frozen=True)
class ToPydanticConversionScenario:
    """Input → expected DTO output for a valid conversion."""

    input: UpdateDeploymentPolicyInputGQL
    expected_rolling_update: RollingUpdateConfigInput | None
    expected_blue_green: BlueGreenConfigInput | None


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
def mock_upsert_policy() -> AsyncMock:
    """Create mock deployment upsert_policy adapter method."""
    return AsyncMock()


@pytest.fixture
def mock_info(mock_upsert_policy: AsyncMock) -> MagicMock:
    """Create mock strawberry.Info with deployment adapters."""
    info = MagicMock()
    info.context.adapters.deployment.upsert_policy = mock_upsert_policy
    return info


@pytest.fixture
def rolling_update_input() -> UpdateDeploymentPolicyInputGQL:
    """Input for ROLLING strategy with custom surge/unavailable."""
    return UpdateDeploymentPolicyInputGQL(
        deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
        strategy=DeploymentStrategy.ROLLING,
        rolling_update=RollingUpdateConfigInputGQL(
            max_surge=IntOrPercentInputGQL(count=2),
            max_unavailable=IntOrPercentInputGQL(count=1),
        ),
    )


def _make_policy_node_dto(
    *,
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING,
    rolling_update: RollingUpdateConfigInfo | None = None,
    blue_green: BlueGreenConfigInfo | None = None,
) -> DeploymentPolicyNodeDTO:
    """Create a DeploymentPolicyNode DTO for mock results."""
    if strategy == DeploymentStrategy.ROLLING:
        surge = rolling_update.max_surge if rolling_update is not None else _int_or_percent(1)
        unavailable = (
            rolling_update.max_unavailable if rolling_update is not None else _int_or_percent(0)
        )
        strategy_spec: RollingUpdateStrategySpecInfo | BlueGreenStrategySpecInfo = (
            RollingUpdateStrategySpecInfo(
                strategy=strategy,
                max_surge=surge,
                max_unavailable=unavailable,
            )
        )
    else:
        promote = blue_green.auto_promote if blue_green is not None else False
        delay = blue_green.promote_delay_seconds if blue_green is not None else 0
        strategy_spec = BlueGreenStrategySpecInfo(
            strategy=strategy,
            auto_promote=promote,
            promote_delay_seconds=delay,
        )
    return DeploymentPolicyNodeDTO(
        id=uuid.uuid4(),
        deployment_id=uuid.UUID(SAMPLE_DEPLOYMENT_ID),
        strategy_spec=strategy_spec,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


# --- Input type conversion tests ---


class TestToPydanticConversion:
    """Tests for UpdateDeploymentPolicyInputGQL.to_pydantic()."""

    @pytest.mark.parametrize(
        "scenario",
        [
            pytest.param(
                ToPydanticConversionScenario(
                    input=UpdateDeploymentPolicyInputGQL(
                        deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
                        strategy=DeploymentStrategy.ROLLING,
                        rolling_update=RollingUpdateConfigInputGQL(
                            max_surge=IntOrPercentInputGQL(count=2),
                            max_unavailable=IntOrPercentInputGQL(count=1),
                        ),
                    ),
                    expected_rolling_update=RollingUpdateConfigInput(
                        max_surge=_int_or_percent(2), max_unavailable=_int_or_percent(1)
                    ),
                    expected_blue_green=None,
                ),
                id="rolling",
            ),
            pytest.param(
                ToPydanticConversionScenario(
                    input=UpdateDeploymentPolicyInputGQL(
                        deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
                        strategy=DeploymentStrategy.BLUE_GREEN,
                        blue_green=BlueGreenConfigInputGQL(
                            auto_promote=True, promote_delay_seconds=30
                        ),
                    ),
                    expected_rolling_update=None,
                    expected_blue_green=BlueGreenConfigInput(
                        auto_promote=True, promote_delay_seconds=30
                    ),
                ),
                id="blue_green",
            ),
        ],
    )
    def test_converts_gql_input_to_dto(self, scenario: ToPydanticConversionScenario) -> None:
        """Test that GQL input is correctly converted to UpsertDeploymentPolicyInput DTO."""
        dto = scenario.input.to_pydantic()

        assert dto.strategy == scenario.input.strategy
        assert dto.rolling_update == scenario.expected_rolling_update
        assert dto.blue_green == scenario.expected_blue_green

    def test_converts_deployment_id_to_uuid(self) -> None:
        """Test that string deployment_id is correctly parsed into UUID."""
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID(SAMPLE_DEPLOYMENT_ID),
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=RollingUpdateConfigInputGQL(),
        )
        dto = input_gql.to_pydantic()

        assert str(dto.deployment_id) == SAMPLE_DEPLOYMENT_ID


# --- Resolver tests ---


class TestAdminUpdateDeploymentPolicyResolver:
    """Tests for update_deployment_policy resolver."""

    async def test_delegates_upsert_action_to_adapter(
        self,
        mock_superadmin_user: MagicMock,
        mock_upsert_policy: AsyncMock,
        mock_info: MagicMock,
        rolling_update_input: UpdateDeploymentPolicyInputGQL,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that resolver delegates to adapter and returns payload."""
        # Given
        policy_node = _make_policy_node_dto(
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=RollingUpdateConfigInfo(
                max_surge=_int_or_percent(2), max_unavailable=_int_or_percent(1)
            ),
        )
        mock_upsert_policy.return_value = UpsertDeploymentPolicyPayloadDTO(policy=policy_node)

        monkeypatch.setattr(
            gql_utils,
            "current_user",
            lambda: mock_superadmin_user,
        )

        # When
        resolver_fn = policy_resolver.update_deployment_policy.base_resolver
        result = await resolver_fn(rolling_update_input, mock_info)

        # Then
        mock_upsert_policy.assert_called_once()
        call_args = mock_upsert_policy.call_args
        dto: UpsertDeploymentPolicyInput = call_args[0][0]

        assert str(dto.deployment_id) == SAMPLE_DEPLOYMENT_ID
        assert dto.strategy == DeploymentStrategy.ROLLING

        assert isinstance(result, UpdateDeploymentPolicyPayloadGQL)

    async def test_rejects_non_superadmin(
        self,
        mock_regular_user: MagicMock,
        mock_upsert_policy: AsyncMock,
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

        mock_upsert_policy.assert_not_called()
