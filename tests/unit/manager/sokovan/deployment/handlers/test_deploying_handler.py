"""Regression test for BA-5557.

A deployment created without a revision skips check_pending (which normally
registers the appproxy endpoint).  When ActivateRevision later sets
deploying_revision_id and transitions the deployment to DEPLOYING,
execute() must register the endpoint before route provisioning begins.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.sokovan.deployment.handlers.deploying import (
    DeployingProvisioningHandler,
)
from ai.backend.manager.sokovan.deployment.strategy.applier import StrategyApplyResult
from ai.backend.manager.sokovan.deployment.strategy.types import StrategyEvaluationSummary
from ai.backend.manager.sokovan.deployment.types import DeploymentWithHistory


async def test_execute_registers_endpoint_for_deployment_without_revision(
    deploying_provisioning_handler: DeployingProvisioningHandler,
    mock_deployment_repo: AsyncMock,
    mock_deployment_executor: AsyncMock,
    mock_evaluator: AsyncMock,
    mock_applier: AsyncMock,
    deployment_created_without_revision: DeploymentWithHistory,
    proxy_target: ScalingGroupProxyTarget,
) -> None:
    """BA-5557: execute() registers appproxy endpoint for a deployment that
    was created without a revision and later ActivateRevision'd into DEPLOYING."""
    mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
        "default": proxy_target,
    }
    mock_evaluator.evaluate.return_value = StrategyEvaluationSummary()
    mock_applier.apply.return_value = StrategyApplyResult()

    await deploying_provisioning_handler.execute([deployment_created_without_revision])

    info = deployment_created_without_revision.deployment_info
    mock_deployment_executor.register_endpoint.assert_awaited_once_with(
        info, proxy_target, info.deploying_revision_id
    )
    mock_deployment_repo.update_endpoint_urls_bulk.assert_awaited_once()
