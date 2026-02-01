from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    RuleId,
)
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
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
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.scenario import ScenarioBase


class TestModifyAutoScalingRule:
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
    def mock_check_user_access_modify(self, mocker: Any, auto_scaling_service: Any) -> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
                auto_scaling_service,
                "check_user_access",
                new_callable=AsyncMock,
            ),
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_get_auto_scaling_rule_by_id(self, mocker: Any, mock_repositories: Any) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_auto_scaling_rule_by_id",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_get_endpoint_access_validation_data_modify(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_endpoint_access_validation_data",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_modify_auto_scaling_rule(self, mocker: Any, mock_repositories: Any) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "update_auto_scaling_rule",
                new_callable=AsyncMock,
            ),
        )

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "Modify threshold",
                ModifyEndpointAutoScalingRuleAction(
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
        ],
    )
    @pytest.mark.asyncio
    async def test_modify_auto_scaling_rule(
        self,
        scenario: ScenarioBase[
            ModifyEndpointAutoScalingRuleAction, ModifyEndpointAutoScalingRuleActionResult
        ],
        user_data: UserData,
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_check_user_access_modify: AsyncMock,
        mock_get_auto_scaling_rule_by_id: AsyncMock,
        mock_get_endpoint_access_validation_data_modify: AsyncMock,
        mock_modify_auto_scaling_rule: AsyncMock,
    ) -> None:
        action = scenario.input

        # Mock repository responses based on scenario
        if scenario.description in [
            "Modify threshold",
            "Modify min/max replicas",
            "Disable rule",
        ]:
            # Create a mock rule with endpoint field
            mock_rule = MagicMock(
                id=action.id,
                metric_source=AutoScalingMetricSource.KERNEL,
                metric_name="cpu_utilization",
                threshold="70.0",
                comparator=AutoScalingMetricComparator.GREATER_THAN,
                step_size=1,
                cooldown_seconds=300,
                min_replicas=2,
                max_replicas=10,
                created_at=datetime.now(tz=UTC),
                last_triggered_at=None,
                endpoint=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            )
            mock_get_auto_scaling_rule_by_id.return_value = mock_rule

            # Mock validation data for access validation
            mock_validation_data = MagicMock(
                session_owner_id=user_data.user_id,
                session_owner_role=UserRole(user_data.role),
                domain=user_data.domain_name,
            )
            mock_get_endpoint_access_validation_data_modify.return_value = mock_validation_data
            mock_modify_auto_scaling_rule.return_value = mock_rule

        elif scenario.description == "Rule not found":
            mock_get_auto_scaling_rule_by_id.return_value = None
            mock_modify_auto_scaling_rule.return_value = None

        async def modify_auto_scaling_rule(
            action: ModifyEndpointAutoScalingRuleAction,
        ) -> ModifyEndpointAutoScalingRuleActionResult:
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
        result = await modify_auto_scaling_rule(action)
        assert result.success is True
        expected = scenario.expected
        if expected and expected.data:
            assert result.data is not None
            assert result.data.id == expected.data.id
