import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    RuleId,
)
from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.model_serving.updaters import (
    EndpointAutoScalingRuleUpdaterSpec,
)
from ai.backend.manager.services.model_serving.actions.modify_auto_scaling_rule import (
    ModifyEndpointAutoScalingRuleAction,
    ModifyEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.exceptions import (
    EndpointAutoScalingRuleNotFound,
)
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.manager.types import OptionalState, TriState

from ...utils import ScenarioBase


@pytest.fixture
def mock_check_requester_access_modify(mocker, auto_scaling_service):
    mock = mocker.patch.object(
        auto_scaling_service,
        "check_requester_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_auto_scaling_rule_by_id(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_auto_scaling_rule_by_id_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_modify_auto_scaling_rule(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "update_auto_scaling_rule_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_update_auto_scaling_rule_force(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "update_auto_scaling_rule_force",
        new_callable=AsyncMock,
    )
    return mock


class TestModifyAutoScalingRule:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "Modify threshold",
                ModifyEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000005"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    id=RuleId(uuid.UUID("88888888-8888-8888-8888-888888888888")),
                    updater=Updater(
                        spec=EndpointAutoScalingRuleUpdaterSpec(
                            threshold=OptionalState.update(Decimal("85.0")),
                        ),
                        pk_value=uuid.UUID("88888888-8888-8888-8888-888888888888"),
                    ),
                ),
                ModifyEndpointAutoScalingRuleActionResult(
                    success=True,
                    data=MagicMock(id=uuid.UUID("88888888-8888-8888-8888-888888888888")),
                ),
            ),
            ScenarioBase.success(
                "Modify min/max replicas",
                ModifyEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000006"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    id=RuleId(uuid.UUID("99999999-9999-9999-9999-999999999999")),
                    updater=Updater(
                        spec=EndpointAutoScalingRuleUpdaterSpec(
                            min_replicas=TriState.update(5),
                            max_replicas=TriState.update(25),
                        ),
                        pk_value=uuid.UUID("99999999-9999-9999-9999-999999999999"),
                    ),
                ),
                ModifyEndpointAutoScalingRuleActionResult(
                    success=True,
                    data=MagicMock(id=uuid.UUID("99999999-9999-9999-9999-999999999999")),
                ),
            ),
            ScenarioBase.success(
                "Disable rule",
                ModifyEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000007"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    id=RuleId(uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
                    updater=Updater(
                        spec=EndpointAutoScalingRuleUpdaterSpec(),
                        pk_value=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                    ),
                ),
                ModifyEndpointAutoScalingRuleActionResult(
                    success=True,
                    data=MagicMock(id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
                ),
            ),
            ScenarioBase.failure(
                "Rule not found",
                ModifyEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000008"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    id=RuleId(uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
                    updater=Updater(
                        spec=EndpointAutoScalingRuleUpdaterSpec(
                            threshold=OptionalState.update(Decimal("90.0")),
                        ),
                        pk_value=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                    ),
                ),
                EndpointAutoScalingRuleNotFound,
            ),
            ScenarioBase.success(
                "SUPERADMIN modify all parameters",
                ModifyEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000012"),
                        user_role=UserRole.SUPERADMIN,
                        domain_name="default",
                    ),
                    id=RuleId(uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")),
                    updater=Updater(
                        spec=EndpointAutoScalingRuleUpdaterSpec(
                            threshold=OptionalState.update(Decimal("75.0")),
                            min_replicas=TriState.update(3),
                            max_replicas=TriState.update(30),
                            step_size=OptionalState.update(3),
                            cooldown_seconds=OptionalState.update(180),
                        ),
                        pk_value=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
                    ),
                ),
                ModifyEndpointAutoScalingRuleActionResult(
                    success=True,
                    data=MagicMock(id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")),
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_modify_auto_scaling_rule(
        self,
        scenario: ScenarioBase[
            ModifyEndpointAutoScalingRuleAction, ModifyEndpointAutoScalingRuleActionResult
        ],
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_check_requester_access_modify,
        mock_get_auto_scaling_rule_by_id,
        mock_modify_auto_scaling_rule,
        mock_update_auto_scaling_rule_force,
    ):
        # Mock repository responses based on scenario
        if scenario.description in [
            "Modify threshold",
            "Modify min/max replicas",
            "Disable rule",
            "SUPERADMIN modify all parameters",
        ]:
            # Create a mock that has from_row method
            mock_rule = MagicMock(
                id=scenario.input.id,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu_utilization",
                threshold="70.0",
                comparator=AutoScalingMetricComparator.GREATER_THAN,
                step_size=1,
                cooldown_seconds=300,
                min_replicas=2,
                max_replicas=10,
                created_at=datetime.now(),
                last_triggered_at=None,
                endpoint=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            )
            mock_get_auto_scaling_rule_by_id.return_value = mock_rule
            mock_modify_auto_scaling_rule.return_value = mock_rule
            mock_update_auto_scaling_rule_force.return_value = mock_rule

        elif scenario.description == "Rule not found":
            mock_get_auto_scaling_rule_by_id.return_value = None
            mock_modify_auto_scaling_rule.return_value = None

        async def modify_auto_scaling_rule(action: ModifyEndpointAutoScalingRuleAction):
            return (
                await auto_scaling_processors.modify_endpoint_auto_scaling_rule.wait_for_complete(
                    action
                )
            )

        # For failure scenarios, expect exception
        if scenario.expected_exception is not None:
            await scenario.test(modify_auto_scaling_rule)
            return

        # For success scenarios, call the action and verify the result
        result = await modify_auto_scaling_rule(scenario.input)
        assert result.success is True
        expected = scenario.expected
        if expected and expected.data:
            assert result.data is not None
            assert result.data.id == expected.data.id
