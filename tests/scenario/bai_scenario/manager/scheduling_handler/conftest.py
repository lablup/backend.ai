"""The scheduling handler adapter, assembled for one row.

The adapter answers from the handlers its coordinator registers, so each fixture is the
adapter over the coordinator that row stands on.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from ai.backend.manager.api.adapters.scheduling_handler.adapter import SchedulingHandlerAdapter
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.handlers.base import DeploymentHandler
from ai.backend.manager.sokovan.deployment.handlers.deploying_initializing import (
    DeployingInitializingHandler,
)
from ai.backend.manager.sokovan.deployment.handlers.replica import CheckReplicaDeploymentHandler
from bai_scenario.fakes.deployment import FakeDeploymentCoordinator
from bai_scenario.runner.unwired import unwired


@pytest.fixture
def deployment_handlers() -> Sequence[DeploymentHandler]:
    """등록된 배포 처리기. 이름, 분류, 설명만 읽으므로 안쪽은 배선하지 않는다."""
    executor = unwired(DeploymentExecutor, "처리기의 이름, 분류, 설명만 읽는다")
    controller = unwired(DeploymentController, "처리기의 이름, 분류, 설명만 읽는다")
    return (
        CheckReplicaDeploymentHandler(
            deployment_executor=executor, deployment_controller=controller
        ),
        DeployingInitializingHandler(
            deployment_controller=controller, deployment_executor=executor
        ),
    )


@pytest.fixture
def adapter(deployment_handlers: Sequence[DeploymentHandler]) -> SchedulingHandlerAdapter:
    return SchedulingHandlerAdapter(FakeDeploymentCoordinator(deployment_handlers))


@pytest.fixture
def adapter_with_no_handler_registered() -> SchedulingHandlerAdapter:
    return SchedulingHandlerAdapter(FakeDeploymentCoordinator(()))
