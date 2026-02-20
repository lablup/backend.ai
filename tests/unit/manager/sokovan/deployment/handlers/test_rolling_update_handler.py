"""Unit tests for RollingUpdateDeploymentHandler.

Verifies handler wrapper behavior:
- Target statuses = [DEPLOYING]
- Post-process marks PROVISIONING for successes
- Post-process re-marks ROLLING_UPDATE for skipped (in-progress)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.manager.data.deployment.types import (
    DeploymentStatusTransitions,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.handlers.rolling_update import (
    RollingUpdateDeploymentHandler,
)
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentLifecycleType,
)


@pytest.fixture
def mock_executor() -> AsyncMock:
    executor = AsyncMock()
    executor.execute_rolling_update_cycle = AsyncMock(return_value=DeploymentExecutionResult())
    return executor


@pytest.fixture
def mock_controller() -> AsyncMock:
    controller = AsyncMock()
    controller.mark_lifecycle_needed = AsyncMock()
    return controller


@pytest.fixture
def mock_route_controller() -> AsyncMock:
    controller = AsyncMock()
    controller.mark_lifecycle_needed = AsyncMock()
    return controller


@pytest.fixture
def handler(
    mock_executor: AsyncMock,
    mock_controller: AsyncMock,
    mock_route_controller: AsyncMock,
) -> RollingUpdateDeploymentHandler:
    return RollingUpdateDeploymentHandler(
        deployment_executor=mock_executor,
        deployment_controller=mock_controller,
        route_controller=mock_route_controller,
    )


class TestRollingUpdateDeploymentHandler:
    """Tests for RollingUpdateDeploymentHandler."""

    def test_name(self, handler: RollingUpdateDeploymentHandler) -> None:
        assert handler.name() == "rolling-update-deployments"

    def test_lock_id(self, handler: RollingUpdateDeploymentHandler) -> None:
        assert handler.lock_id == LockID.LOCKID_DEPLOYMENT_ROLLING_UPDATE

    def test_target_statuses(self, handler: RollingUpdateDeploymentHandler) -> None:
        assert handler.target_statuses() == [EndpointLifecycle.DEPLOYING]

    def test_next_status(self, handler: RollingUpdateDeploymentHandler) -> None:
        assert handler.next_status() == EndpointLifecycle.READY

    def test_failure_status(self, handler: RollingUpdateDeploymentHandler) -> None:
        assert handler.failure_status() is None

    def test_status_transitions(self, handler: RollingUpdateDeploymentHandler) -> None:
        transitions = handler.status_transitions()
        assert transitions == DeploymentStatusTransitions(
            success=EndpointLifecycle.READY,
            failure=None,
        )

    async def test_execute_delegates_to_executor(
        self,
        handler: RollingUpdateDeploymentHandler,
        mock_executor: AsyncMock,
    ) -> None:
        deployments = [MagicMock()]
        await handler.execute(deployments)
        mock_executor.execute_rolling_update_cycle.assert_awaited_once_with(deployments)

    async def test_post_process_marks_provisioning_for_successes(
        self,
        handler: RollingUpdateDeploymentHandler,
        mock_route_controller: AsyncMock,
        mock_controller: AsyncMock,
    ) -> None:
        """When there are successes, marks PROVISIONING for route lifecycle."""
        result = DeploymentExecutionResult(
            successes=[MagicMock()],
            skipped=[],
        )
        await handler.post_process(result)
        mock_route_controller.mark_lifecycle_needed.assert_awaited()

    async def test_post_process_marks_rolling_update_for_skipped(
        self,
        handler: RollingUpdateDeploymentHandler,
        mock_controller: AsyncMock,
        mock_route_controller: AsyncMock,
    ) -> None:
        """When there are skipped (in-progress), re-marks ROLLING_UPDATE."""
        result = DeploymentExecutionResult(
            successes=[],
            skipped=[MagicMock()],
        )
        await handler.post_process(result)
        mock_controller.mark_lifecycle_needed.assert_awaited_with(
            DeploymentLifecycleType.ROLLING_UPDATE
        )

    async def test_post_process_no_action_when_empty(
        self,
        handler: RollingUpdateDeploymentHandler,
        mock_controller: AsyncMock,
        mock_route_controller: AsyncMock,
    ) -> None:
        """When no successes or skipped, no lifecycle marks."""
        result = DeploymentExecutionResult(
            successes=[],
            skipped=[],
        )
        await handler.post_process(result)
        mock_controller.mark_lifecycle_needed.assert_not_awaited()
        mock_route_controller.mark_lifecycle_needed.assert_not_awaited()
