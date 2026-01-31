from __future__ import annotations

from typing import Any
import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import RuleId
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
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
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService
from ai.backend.testutils.scenario import ScenarioBase


class TestDeleteAutoScalingRule:
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
    def mock_check_user_access_delete_rule(self, mocker: Any, auto_scaling_service: Any)-> AsyncMock:
        mock = mocker.patch.object(
            auto_scaling_service,
            "check_user_access",
            new_callable=AsyncMock,
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_get_auto_scaling_rule_by_id_delete_rule(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_auto_scaling_rule_by_id",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_get_endpoint_access_validation_data_delete_rule(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_access_validation_data",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_delete_auto_scaling_rule(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "delete_auto_scaling_rule",
            new_callable=AsyncMock,
        )

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
        mock_check_user_access_delete_rule: AsyncMock,
        mock_get_auto_scaling_rule_by_id_delete_rule: AsyncMock,
        mock_get_endpoint_access_validation_data_delete_rule: AsyncMock,
        mock_delete_auto_scaling_rule: AsyncMock,
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

        async def delete_auto_scaling_rule(action: DeleteEndpointAutoScalingRuleAction) -> DeleteEndpointAutoScalingRuleActionResult:
            return (
                await auto_scaling_processors.delete_endpoint_auto_scaling_rule.wait_for_complete(
                    action
                )
            )

        await scenario.test(delete_auto_scaling_rule)
