import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import RuleId
from ai.backend.manager.data.model_serving.types import RequesterCtx
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

from ...utils import ScenarioBase


@pytest.fixture
def mock_check_requester_access_delete(mocker, auto_scaling_service):
    mock = mocker.patch.object(
        auto_scaling_service,
        "check_requester_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_auto_scaling_rule_by_id_delete(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_auto_scaling_rule_by_id_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_delete_auto_scaling_rule(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "delete_auto_scaling_rule_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_delete_auto_scaling_rule_force(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "delete_auto_scaling_rule_force",
        new_callable=AsyncMock,
    )
    return mock


class TestDeleteAutoScalingRule:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "Normal delete",
                DeleteEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000009"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    id=RuleId(uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")),
                ),
                DeleteEndpointAutoScalingRuleActionResult(
                    success=True,
                ),
            ),
            ScenarioBase.failure(
                "Rule not found",
                DeleteEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    id=RuleId(uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")),
                ),
                EndpointAutoScalingRuleNotFound,
            ),
            ScenarioBase.success(
                "SUPERADMIN delete",
                DeleteEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000013"),
                        user_role=UserRole.SUPERADMIN,
                        domain_name="default",
                    ),
                    id=RuleId(uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")),
                ),
                DeleteEndpointAutoScalingRuleActionResult(
                    success=True,
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_delete_auto_scaling_rule(
        self,
        scenario: ScenarioBase[
            DeleteEndpointAutoScalingRuleAction, DeleteEndpointAutoScalingRuleActionResult
        ],
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_check_requester_access_delete,
        mock_get_auto_scaling_rule_by_id_delete,
        mock_delete_auto_scaling_rule,
        mock_delete_auto_scaling_rule_force,
    ):
        # Mock repository responses based on scenario
        if scenario.description in ["Normal delete", "SUPERADMIN delete"]:
            mock_rule = MagicMock(
                id=scenario.input.id,
                enabled=True,
            )
            mock_get_auto_scaling_rule_by_id_delete.return_value = mock_rule
            mock_delete_auto_scaling_rule.return_value = True
            mock_delete_auto_scaling_rule_force.return_value = True

        elif scenario.description == "Rule not found":
            mock_get_auto_scaling_rule_by_id_delete.return_value = None
            mock_delete_auto_scaling_rule.return_value = False

        async def delete_auto_scaling_rule(action: DeleteEndpointAutoScalingRuleAction):
            return (
                await auto_scaling_processors.delete_endpoint_auto_scaling_rule.wait_for_complete(
                    action
                )
            )

        await scenario.test(delete_auto_scaling_rule)
