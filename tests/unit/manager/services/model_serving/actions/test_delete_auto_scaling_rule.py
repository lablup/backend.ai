import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.user.types import UserData
from ai.backend.common.types import RuleId
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.delete_auto_scaling_rule import (
    DeleteEndpointAutoScalingRuleAction,
    DeleteEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.exceptions import (
    EndpointAutoScalingRuleNotFound,
)
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.testutils.scenario import ScenarioBase


@pytest.fixture
def mock_check_user_access_delete_rule(mocker, auto_scaling_service):
    mock = mocker.patch.object(
        auto_scaling_service,
        "check_user_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_auto_scaling_rule_by_id_delete_rule(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "get_auto_scaling_rule_by_id",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_get_endpoint_access_validation_data_delete_rule(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_access_validation_data",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_delete_auto_scaling_rule(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "delete_auto_scaling_rule",
        new_callable=AsyncMock,
    )


class TestDeleteAutoScalingRule:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "Normal delete",
                DeleteEndpointAutoScalingRuleAction(
                    id=RuleId(uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")),
                ),
                DeleteEndpointAutoScalingRuleActionResult(
                    success=True,
                ),
            ),
            ScenarioBase.failure(
                "Rule not found",
                DeleteEndpointAutoScalingRuleAction(
                    id=RuleId(uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")),
                ),
                EndpointAutoScalingRuleNotFound,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_delete_auto_scaling_rule(
        self,
        scenario: ScenarioBase[
            DeleteEndpointAutoScalingRuleAction, DeleteEndpointAutoScalingRuleActionResult
        ],
        user_data: UserData,
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_check_user_access_delete_rule,
        mock_get_auto_scaling_rule_by_id_delete_rule,
        mock_get_endpoint_access_validation_data_delete_rule,
        mock_delete_auto_scaling_rule,
    ) -> None:
        action = scenario.input

        # Mock repository responses based on scenario
        if scenario.description == "Normal delete":
            mock_rule = MagicMock(
                id=action.id,
                enabled=True,
                endpoint=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            )
            mock_get_auto_scaling_rule_by_id_delete_rule.return_value = mock_rule

            mock_validation_data = MagicMock(
                session_owner_id=user_data.user_id,
                session_owner_role=UserRole(user_data.role),
                domain=user_data.domain_name,
            )
            mock_get_endpoint_access_validation_data_delete_rule.return_value = mock_validation_data
            mock_delete_auto_scaling_rule.return_value = True

        elif scenario.description == "Rule not found":
            mock_get_auto_scaling_rule_by_id_delete_rule.return_value = None
            mock_delete_auto_scaling_rule.return_value = False

        async def delete_auto_scaling_rule(action: DeleteEndpointAutoScalingRuleAction):
            return (
                await auto_scaling_processors.delete_endpoint_auto_scaling_rule.wait_for_complete(
                    action
                )
            )

        await scenario.test(delete_auto_scaling_rule)
