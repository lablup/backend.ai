from __future__ import annotations

from typing import Any
import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    EndpointId,
)
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.data.model_serving.creator import EndpointAutoScalingRuleCreator
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
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
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService
from ai.backend.testutils.scenario import ScenarioBase


class TestCreateEndpointAutoScalingRule:
    @pytest.fixture
    def user_data(self) -> UserData:
        return UserData(
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    @pytest.fixture(autouse=True)
    def set_user_context(self, user_data: UserData) -> Iterator[None]:
        with with_user(user_data):
            yield

    @pytest.fixture
    def mock_action_monitor(self) -> MagicMock:
        return MagicMock(spec=ActionMonitor)

    @pytest.fixture
    def mock_repositories(self) -> MagicMock:
        mock = MagicMock(spec=ModelServingRepositories)
        mock.repository = MagicMock(spec=ModelServingRepository)
        return mock

    @pytest.fixture
    def auto_scaling_service(
        self,
        mock_repositories: MagicMock,
    ) -> AutoScalingService:
        return AutoScalingService(
            repository=mock_repositories.repository,
        )

    @pytest.fixture
    def auto_scaling_processors(
        self,
        mock_action_monitor: MagicMock,
        auto_scaling_service: AutoScalingService,
    ) -> ModelServingAutoScalingProcessors:
        return ModelServingAutoScalingProcessors(
            service=auto_scaling_service,
            action_monitors=[mock_action_monitor],
        )

    @pytest.fixture
    def mock_check_user_access_create(self, mocker: Any, auto_scaling_service: Any)-> AsyncMock:
        mock = mocker.patch.object(
            auto_scaling_service,
            "check_user_access",
            new_callable=AsyncMock,
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_get_endpoint_access_validation_data_create(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_access_validation_data",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_create_auto_scaling_rule(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "create_auto_scaling_rule",
            new_callable=AsyncMock,
        )

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "CPU based scaling",
                CreateEndpointAutoScalingRuleAction(
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
                "Memory utilization based scaling",
                CreateEndpointAutoScalingRuleAction(
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
        user_data: UserData,
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_check_user_access_create: AsyncMock,
        mock_get_endpoint_access_validation_data_create: AsyncMock,
        mock_create_auto_scaling_rule: AsyncMock,
    ) -> None:
        action = scenario.input

        # Mock repository responses based on scenario
        if scenario.description in [
            "CPU based scaling",
            "Request count based scaling",
            "Custom metric",
            "Memory utilization based scaling",
        ]:
            mock_validation_data = MagicMock(
                session_owner_id=user_data.user_id,
                session_owner_role=UserRole(user_data.role),
                domain=user_data.domain_name,
            )
            mock_get_endpoint_access_validation_data_create.return_value = mock_validation_data

            expected_result = scenario.expected
            assert expected_result is not None
            mock_rule = MagicMock(
                id=expected_result.data.id if expected_result.data else None,
                endpoint_id=action.endpoint_id,
                metric_source=action.creator.metric_source,
                metric_name=action.creator.metric_name,
                threshold=action.creator.threshold,
                comparator=action.creator.comparator,
                step_size=action.creator.step_size,
                cooldown_seconds=action.creator.cooldown_seconds,
                min_replicas=action.creator.min_replicas,
                max_replicas=action.creator.max_replicas,
                enabled=True,
            )
            mock_create_auto_scaling_rule.return_value = mock_rule

        elif scenario.description == "Endpoint not found":
            mock_get_endpoint_access_validation_data_create.return_value = None
            mock_create_auto_scaling_rule.return_value = None

        async def create_auto_scaling_rule(action: CreateEndpointAutoScalingRuleAction) -> CreateEndpointAutoScalingRuleActionResult:
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
        result = await create_auto_scaling_rule(action)
        assert result.success is True
        expected = scenario.expected
        if expected and expected.data:
            assert result.data is not None
            assert result.data.id == expected.data.id
