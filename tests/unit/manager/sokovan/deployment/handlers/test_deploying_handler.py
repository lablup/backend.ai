"""Regression test for BA-5557.

A deployment created without a revision skips check_pending (which normally
registers the appproxy endpoint).  When ActivateRevision later sets
deploying_revision_id and transitions the deployment to DEPLOYING,
execute() must register the endpoint before route provisioning begins.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ReplicaSpec,
)
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.sokovan.deployment.handlers.deploying import (
    DeployingProvisioningHandler,
)
from ai.backend.manager.sokovan.deployment.strategy.applier import StrategyApplyResult
from ai.backend.manager.sokovan.deployment.strategy.types import StrategyEvaluationSummary
from ai.backend.manager.sokovan.deployment.types import DeploymentWithHistory


class TestDeployingProvisioningHandler:
    """Tests for DeployingProvisioningHandler."""

    @pytest.fixture
    def mock_deployment_repo(self) -> AsyncMock:
        repo = AsyncMock()
        repo.fetch_scaling_group_proxy_targets = AsyncMock(return_value={})
        repo.update_endpoint_urls_bulk = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def mock_deployment_executor(self) -> AsyncMock:
        executor = AsyncMock()
        mock_revision_spec = MagicMock()
        mock_revision_spec.execution.runtime_variant = RuntimeVariant.CUSTOM
        executor.register_endpoint = AsyncMock(return_value="http://endpoint.test/v1")
        return executor

    @pytest.fixture
    def mock_evaluator(self) -> AsyncMock:
        evaluator = AsyncMock()
        evaluator.evaluate.return_value = StrategyEvaluationSummary()
        return evaluator

    @pytest.fixture
    def mock_applier(self) -> AsyncMock:
        applier = AsyncMock()
        applier.apply.return_value = StrategyApplyResult()
        return applier

    @pytest.fixture
    def handler(
        self,
        mock_deployment_executor: AsyncMock,
        mock_deployment_repo: AsyncMock,
        mock_evaluator: AsyncMock,
        mock_applier: AsyncMock,
    ) -> DeployingProvisioningHandler:
        return DeployingProvisioningHandler(
            deployment_controller=AsyncMock(),
            route_controller=AsyncMock(),
            evaluator=mock_evaluator,
            applier=mock_applier,
            deployment_executor=mock_deployment_executor,
            deployment_repo=mock_deployment_repo,
        )

    @pytest.fixture
    def proxy_target(self) -> ScalingGroupProxyTarget:
        return ScalingGroupProxyTarget(
            addr="http://proxy:8080",
            api_token="test-token",
        )

    @pytest.fixture
    def deployment_created_without_revision(self) -> DeploymentWithHistory:
        """Deployment created without a revision, then ActivateRevision'd into DEPLOYING.

        current_revision_id is None (no initial revision), deploying_revision_id is set
        (ActivateRevision assigned it), and url is None (check_pending was skipped).
        """
        deploying_rev_id = uuid4()
        revision = MagicMock()
        revision.revision_id = deploying_rev_id

        return DeploymentWithHistory(
            deployment_info=DeploymentInfo(
                id=uuid4(),
                metadata=DeploymentMetadata(
                    name="test-deployment",
                    domain="default",
                    project=uuid4(),
                    resource_group="default",
                    created_user=uuid4(),
                    session_owner=uuid4(),
                    created_at=datetime.now(tzutc()),
                    revision_history_limit=10,
                ),
                state=DeploymentState(
                    lifecycle=EndpointLifecycle.DEPLOYING,
                    retry_count=0,
                ),
                replica_spec=ReplicaSpec(
                    replica_count=1,
                    desired_replica_count=1,
                ),
                network=DeploymentNetworkSpec(
                    open_to_public=False,
                    url=None,
                ),
                model_revisions=[revision],
                current_revision_id=None,
                deploying_revision_id=deploying_rev_id,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
            ),
        )

    async def test_registers_endpoint_for_deployment_created_without_revision(
        self,
        handler: DeployingProvisioningHandler,
        mock_deployment_repo: AsyncMock,
        mock_deployment_executor: AsyncMock,
        deployment_created_without_revision: DeploymentWithHistory,
        proxy_target: ScalingGroupProxyTarget,
    ) -> None:
        """BA-5557: execute() registers appproxy endpoint for a deployment that
        was created without a revision and later ActivateRevision'd into DEPLOYING."""
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
            "default": proxy_target,
        }

        await handler.execute([deployment_created_without_revision])

        info = deployment_created_without_revision.deployment_info
        mock_deployment_executor.register_endpoint.assert_awaited_once_with(
            info, proxy_target, info.deploying_revision_id
        )
        mock_deployment_repo.update_endpoint_urls_bulk.assert_awaited_once()
