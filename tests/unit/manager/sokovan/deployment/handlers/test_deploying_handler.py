"""Unit tests for DeployingProvisioningHandler._ensure_endpoints_registered.

Verifies that deployments entering DEPLOYING via ActivateRevision
(which skip check_pending) get their appproxy endpoints registered.
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

    async def test_registers_endpoint_for_deployment_without_url(
        self,
        deploying_provisioning_handler: DeployingProvisioningHandler,
        mock_deployment_repo: AsyncMock,
        mock_deployment_executor: AsyncMock,
        deploying_deployment_without_url: DeploymentWithHistory,
        proxy_target: ScalingGroupProxyTarget,
    ) -> None:
        """Deployment without URL gets registered in appproxy."""
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
            "default": proxy_target,
        }

        await deploying_provisioning_handler._ensure_endpoints_registered([
            deploying_deployment_without_url,
        ])

        mock_deployment_executor.register_endpoint.assert_awaited_once()
        mock_deployment_repo.update_endpoint_urls_bulk.assert_awaited_once()

        url_updates = mock_deployment_repo.update_endpoint_urls_bulk.call_args[0][0]
        deployment_id = deploying_deployment_without_url.deployment_info.id
        assert deployment_id in url_updates

    async def test_skips_deployment_already_having_url(
        self,
        deploying_provisioning_handler: DeployingProvisioningHandler,
        mock_deployment_repo: AsyncMock,
        mock_deployment_executor: AsyncMock,
        deploying_deployment_with_url: DeploymentWithHistory,
    ) -> None:
        """Deployment that already has a URL is skipped."""
        await deploying_provisioning_handler._ensure_endpoints_registered([
            deploying_deployment_with_url,
        ])

        mock_deployment_executor.register_endpoint.assert_not_awaited()
        mock_deployment_repo.update_endpoint_urls_bulk.assert_not_awaited()

    async def test_registration_failure_does_not_update_url(
        self,
        deploying_provisioning_handler: DeployingProvisioningHandler,
        mock_deployment_repo: AsyncMock,
        mock_deployment_executor: AsyncMock,
        deploying_deployment_without_url: DeploymentWithHistory,
        proxy_target: ScalingGroupProxyTarget,
    ) -> None:
        """Failed registration does not produce a URL update."""
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
            "default": proxy_target,
        }
        mock_deployment_executor.register_endpoint.side_effect = RuntimeError("Registration failed")

        await deploying_provisioning_handler._ensure_endpoints_registered([
            deploying_deployment_without_url,
        ])

        mock_deployment_repo.update_endpoint_urls_bulk.assert_not_awaited()

    async def test_no_proxy_target_skips_registration(
        self,
        deploying_provisioning_handler: DeployingProvisioningHandler,
        mock_deployment_repo: AsyncMock,
        mock_deployment_executor: AsyncMock,
        deploying_deployment_without_url: DeploymentWithHistory,
    ) -> None:
        """Deployment with no proxy target for its scaling group is skipped."""
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {}

        await deploying_provisioning_handler._ensure_endpoints_registered([
            deploying_deployment_without_url,
        ])

        mock_deployment_executor.register_endpoint.assert_not_awaited()
        mock_deployment_repo.update_endpoint_urls_bulk.assert_not_awaited()
