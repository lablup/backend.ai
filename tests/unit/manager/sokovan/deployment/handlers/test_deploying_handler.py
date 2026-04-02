"""Regression test for BA-5557.

A deployment created without a revision skips check_pending (which normally
registers the appproxy endpoint).  When ActivateRevision later sets
deploying_revision_id and transitions the deployment to DEPLOYING,
_ensure_endpoints_registered must register the endpoint before route
provisioning begins.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.sokovan.deployment.handlers.deploying import (
    DeployingProvisioningHandler,
)
from ai.backend.manager.sokovan.deployment.types import DeploymentWithHistory


async def test_registers_endpoint_when_created_without_revision(
    deploying_provisioning_handler: DeployingProvisioningHandler,
    mock_deployment_repo: AsyncMock,
    mock_deployment_executor: AsyncMock,
    deployment_created_without_revision: DeploymentWithHistory,
    proxy_target: ScalingGroupProxyTarget,
) -> None:
    """BA-5557: deployment created without a revision, then ActivateRevision'd
    into DEPLOYING, gets its appproxy endpoint registered via deploying_revision_id."""
    mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
        "default": proxy_target,
    }

    await deploying_provisioning_handler._ensure_endpoints_registered([
        deployment_created_without_revision,
    ])

    info = deployment_created_without_revision.deployment_info
    mock_deployment_executor.register_endpoint.assert_awaited_once_with(
        info, proxy_target, info.deploying_revision_id
    )
    mock_deployment_repo.update_endpoint_urls_bulk.assert_awaited_once()
