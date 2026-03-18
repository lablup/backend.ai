"""Unit tests for UpdateDeploymentPolicyInputGQL.to_upserter()."""

from __future__ import annotations

import pytest
from strawberry import ID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.api.gql.deployment.types.policy import (
    BlueGreenConfigInputGQL,
    RollingUpdateConfigInputGQL,
    UpdateDeploymentPolicyInputGQL,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec


class TestUpdateDeploymentPolicyInputGQL:
    """Tests for UpdateDeploymentPolicyInputGQL.to_upserter()."""

    def test_rolling_strategy_with_config(self) -> None:
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
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.ROLLING,
        )
        with pytest.raises(InvalidAPIParameters, match="rolling_update"):
            input_gql.to_upserter()

    def test_blue_green_strategy_missing_config_raises(self) -> None:
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.BLUE_GREEN,
        )
        with pytest.raises(InvalidAPIParameters, match="blue_green"):
            input_gql.to_upserter()

    def test_deployment_id_is_converted_to_uuid(self) -> None:
        input_gql = UpdateDeploymentPolicyInputGQL(
            deployment_id=ID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            strategy=DeploymentStrategy.ROLLING,
            rolling_update=RollingUpdateConfigInputGQL(),
        )
        upserter = input_gql.to_upserter()

        assert str(upserter.deployment_id) == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
