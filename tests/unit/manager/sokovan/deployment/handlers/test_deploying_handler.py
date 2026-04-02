"""Unit tests for DeployingProvisioningHandler._ensure_endpoints_registered.

Bug scenario (BA-5557): A deployment created without a revision skips
check_pending (which normally registers the appproxy endpoint).  Later,
ActivateRevision sets deploying_revision_id and transitions the deployment
to DEPLOYING.  _ensure_endpoints_registered must detect this case and
register the endpoint before route provisioning begins.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.sokovan.deployment.handlers.deploying import (
    DeployingProvisioningHandler,
)
from ai.backend.manager.sokovan.deployment.types import DeploymentWithHistory


class TestEnsureEndpointsRegistered:
    """Tests for _ensure_endpoints_registered in DeployingProvisioningHandler."""

    async def test_registers_endpoint_when_created_without_revision(
        self,
        deploying_provisioning_handler: DeployingProvisioningHandler,
        mock_deployment_repo: AsyncMock,
        mock_deployment_executor: AsyncMock,
        deployment_created_without_revision: DeploymentWithHistory,
        proxy_target: ScalingGroupProxyTarget,
    ) -> None:
        """Deployment created without a revision, then ActivateRevision'd into DEPLOYING,
        gets its appproxy endpoint registered via deploying_revision_id."""
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

        url_updates = mock_deployment_repo.update_endpoint_urls_bulk.call_args[0][0]
        assert info.id in url_updates

    async def test_skips_deployment_already_registered(
        self,
        deploying_provisioning_handler: DeployingProvisioningHandler,
        mock_deployment_repo: AsyncMock,
        mock_deployment_executor: AsyncMock,
        deployment_already_registered: DeploymentWithHistory,
    ) -> None:
        """Deployment that already has a URL (went through check_pending) is skipped."""
        await deploying_provisioning_handler._ensure_endpoints_registered([
            deployment_already_registered,
        ])

        mock_deployment_executor.register_endpoint.assert_not_awaited()
        mock_deployment_repo.update_endpoint_urls_bulk.assert_not_awaited()

    async def test_registration_failure_does_not_update_url(
        self,
        deploying_provisioning_handler: DeployingProvisioningHandler,
        mock_deployment_repo: AsyncMock,
        mock_deployment_executor: AsyncMock,
        deployment_created_without_revision: DeploymentWithHistory,
        proxy_target: ScalingGroupProxyTarget,
    ) -> None:
        """Failed appproxy registration does not produce a URL update."""
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
            "default": proxy_target,
        }
        mock_deployment_executor.register_endpoint.side_effect = RuntimeError("Registration failed")

        await deploying_provisioning_handler._ensure_endpoints_registered([
            deployment_created_without_revision,
        ])

        mock_deployment_repo.update_endpoint_urls_bulk.assert_not_awaited()

    async def test_no_proxy_target_skips_registration(
        self,
        deploying_provisioning_handler: DeployingProvisioningHandler,
        mock_deployment_repo: AsyncMock,
        mock_deployment_executor: AsyncMock,
        deployment_created_without_revision: DeploymentWithHistory,
    ) -> None:
        """Deployment with no proxy target for its scaling group is skipped."""
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {}

        await deploying_provisioning_handler._ensure_endpoints_registered([
            deployment_created_without_revision,
        ])

        mock_deployment_executor.register_endpoint.assert_not_awaited()
        mock_deployment_repo.update_endpoint_urls_bulk.assert_not_awaited()
