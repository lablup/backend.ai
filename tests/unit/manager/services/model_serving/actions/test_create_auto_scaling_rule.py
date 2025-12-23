import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointStatus
from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointId,
)
from ai.backend.manager.data.model_serving.creator import EndpointAutoScalingRuleCreator
from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.create_auto_scaling_rule import (
    CreateEndpointAutoScalingRuleAction,
    CreateEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_serving.exceptions import (
    EndpointNotFound,
)
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)

from ...utils import ScenarioBase


@pytest.fixture
def mock_check_requester_access_create(mocker, auto_scaling_service):
    mock = mocker.patch.object(
        auto_scaling_service,
        "check_requester_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_validated_create(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_by_id_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_create_auto_scaling_rule(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "create_auto_scaling_rule_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_create_auto_scaling_rule_force(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "create_auto_scaling_rule_force",
        new_callable=AsyncMock,
    )
    return mock


class TestCreateEndpointAutoScalingRule:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "CPU based scaling",
                CreateEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    endpoint_id=EndpointId(uuid.UUID("11111111-1111-1111-1111-111111111111")),
                    creator=EndpointAutoScalingRuleCreator(
                        metric_source=AutoScalingMetricSource.KERNEL,
                        metric_name="cpu_utilization",
                        threshold="70.0",
                        comparator=AutoScalingMetricComparator.GREATER_THAN,
                        step_size=1,
                        cooldown_seconds=300,
                        min_replicas=2,
                        max_replicas=10,
                    ),
                ),
                CreateEndpointAutoScalingRuleActionResult(
                    success=True,
                    data=MagicMock(id=uuid.UUID("22222222-2222-2222-2222-222222222222")),
                ),
            ),
            ScenarioBase.success(
                "Request count based scaling",
                CreateEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    endpoint_id=EndpointId(uuid.UUID("33333333-3333-3333-3333-333333333333")),
                    creator=EndpointAutoScalingRuleCreator(
                        metric_source=AutoScalingMetricSource.KERNEL,
                        metric_name="requests_per_second",
                        threshold="100.0",
                        comparator=AutoScalingMetricComparator.GREATER_THAN,
                        step_size=2,
                        cooldown_seconds=600,
                        min_replicas=1,
                        max_replicas=20,
                    ),
                ),
                CreateEndpointAutoScalingRuleActionResult(
                    success=True,
                    data=MagicMock(id=uuid.UUID("44444444-4444-4444-4444-444444444444")),
                ),
            ),
            ScenarioBase.success(
                "Custom metric",
                CreateEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    endpoint_id=EndpointId(uuid.UUID("55555555-5555-5555-5555-555555555555")),
                    creator=EndpointAutoScalingRuleCreator(
                        metric_source=AutoScalingMetricSource.INFERENCE_FRAMEWORK,
                        metric_name="queue_length",
                        threshold="50.0",
                        comparator=AutoScalingMetricComparator.GREATER_THAN,
                        step_size=1,
                        cooldown_seconds=180,
                        min_replicas=3,
                        max_replicas=15,
                    ),
                ),
                CreateEndpointAutoScalingRuleActionResult(
                    success=True,
                    data=MagicMock(id=uuid.UUID("66666666-6666-6666-6666-666666666666")),
                ),
            ),
            ScenarioBase.failure(
                "Endpoint not found",
                CreateEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000004"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    endpoint_id=EndpointId(uuid.UUID("77777777-7777-7777-7777-777777777777")),
                    creator=EndpointAutoScalingRuleCreator(
                        metric_source=AutoScalingMetricSource.KERNEL,
                        metric_name="cpu_utilization",
                        threshold="80.0",
                        comparator=AutoScalingMetricComparator.GREATER_THAN,
                        step_size=1,
                        cooldown_seconds=300,
                        min_replicas=1,
                        max_replicas=5,
                    ),
                ),
                EndpointNotFound,
            ),
            ScenarioBase.success(
                "SUPERADMIN CPU based scaling",
                CreateEndpointAutoScalingRuleAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000011"),
                        user_role=UserRole.SUPERADMIN,
                        domain_name="default",
                    ),
                    endpoint_id=EndpointId(uuid.UUID("88888888-8888-8888-8888-888888888888")),
                    creator=EndpointAutoScalingRuleCreator(
                        metric_source=AutoScalingMetricSource.KERNEL,
                        metric_name="memory_utilization",
                        threshold="80.0",
                        comparator=AutoScalingMetricComparator.GREATER_THAN,
                        step_size=2,
                        cooldown_seconds=240,
                        min_replicas=1,
                        max_replicas=15,
                    ),
                ),
                CreateEndpointAutoScalingRuleActionResult(
                    success=True,
                    data=MagicMock(id=uuid.UUID("99999999-9999-9999-9999-999999999999")),
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_create_auto_scaling_rule(
        self,
        scenario: ScenarioBase[
            CreateEndpointAutoScalingRuleAction, CreateEndpointAutoScalingRuleActionResult
        ],
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_check_requester_access_create,
        mock_get_endpoint_by_id_validated_create,
        mock_create_auto_scaling_rule,
        mock_create_auto_scaling_rule_force,
    ):
        # Mock repository responses based on scenario
        if scenario.description in [
            "CPU based scaling",
            "Request count based scaling",
            "Custom metric",
            "SUPERADMIN CPU based scaling",
        ]:
            mock_endpoint = MagicMock(
                id=scenario.input.endpoint_id,
                status=EndpointStatus.READY,
            )
            mock_get_endpoint_by_id_validated_create.return_value = mock_endpoint

            expected_result = scenario.expected
            assert expected_result is not None
            mock_rule = MagicMock(
                id=expected_result.data.id if expected_result.data else None,
                endpoint_id=scenario.input.endpoint_id,
                metric_source=scenario.input.creator.metric_source,
                metric_name=scenario.input.creator.metric_name,
                threshold=scenario.input.creator.threshold,
                comparator=scenario.input.creator.comparator,
                step_size=scenario.input.creator.step_size,
                cooldown_seconds=scenario.input.creator.cooldown_seconds,
                min_replicas=scenario.input.creator.min_replicas,
                max_replicas=scenario.input.creator.max_replicas,
                enabled=True,
            )
            mock_create_auto_scaling_rule.return_value = mock_rule
            mock_create_auto_scaling_rule_force.return_value = mock_rule

        elif scenario.description == "Endpoint not found":
            mock_get_endpoint_by_id_validated_create.return_value = None
            mock_create_auto_scaling_rule.return_value = None

        async def create_auto_scaling_rule(action: CreateEndpointAutoScalingRuleAction):
            return (
                await auto_scaling_processors.create_endpoint_auto_scaling_rule.wait_for_complete(
                    action
                )
            )

        # For failure scenarios, expect exception
        if scenario.expected_exception is not None:
            await scenario.test(create_auto_scaling_rule)
            return

        # For success scenarios, verify success and id
        result = await create_auto_scaling_rule(scenario.input)
        assert result.success is True
        expected = scenario.expected
        if expected and expected.data:
            assert result.data is not None
            assert result.data.id == expected.data.id
