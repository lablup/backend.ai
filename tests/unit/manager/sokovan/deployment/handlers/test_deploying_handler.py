"""Regression test for BA-5557.

A deployment created without a revision skips check_pending (which normally
registers the appproxy endpoint).  When ActivateRevision later sets
deploying_revision_id and transitions the deployment to DEPLOYING,
execute() must register the endpoint before route provisioning begins.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
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
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentWithHistory,
)


class TestDeployingProvisioningHandler:
    """Tests for DeployingProvisioningHandler."""

    @pytest.fixture
    def mock_deployment_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_deployment_executor(self) -> AsyncMock:
        executor = AsyncMock()
        executor.register_endpoints_bulk = AsyncMock(
            side_effect=lambda entries: DeploymentExecutionResult(
                successes=[dep for dep, _ in entries],
            )
        )
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
        mock_deployment_executor: AsyncMock,
        deployment_created_without_revision: DeploymentWithHistory,
    ) -> None:
        """BA-5557: execute() delegates appproxy registration for a deployment
        that was created without a revision and later ActivateRevision'd."""
        await handler.execute([deployment_created_without_revision])

        mock_deployment_executor.register_endpoints_bulk.assert_awaited_once()
        (call_args,) = mock_deployment_executor.register_endpoints_bulk.await_args.args
        assert len(call_args) == 1
        dep, revision_id = call_args[0]
        info = deployment_created_without_revision.deployment_info
        assert dep is deployment_created_without_revision
        assert revision_id == info.deploying_revision_id

    async def test_deployment_already_with_url_is_not_reregistered(
        self,
        handler: DeployingProvisioningHandler,
        mock_deployment_executor: AsyncMock,
        deployment_created_without_revision: DeploymentWithHistory,
    ) -> None:
        """Already-registered deployments must not be re-registered."""
        info = deployment_created_without_revision.deployment_info
        info_with_url = dataclasses.replace(
            info,
            network=dataclasses.replace(info.network, url="http://already-registered/v1"),
        )
        deployment = DeploymentWithHistory(deployment_info=info_with_url)

        await handler.execute([deployment])

        mock_deployment_executor.register_endpoints_bulk.assert_not_awaited()

    async def test_deployment_without_deploying_revision_is_filtered(
        self,
        handler: DeployingProvisioningHandler,
        mock_deployment_executor: AsyncMock,
        deployment_created_without_revision: DeploymentWithHistory,
    ) -> None:
        """Deployments with no deploying_revision_id must be filtered out."""
        info = deployment_created_without_revision.deployment_info
        info_no_rev = dataclasses.replace(info, deploying_revision_id=None)
        deployment = DeploymentWithHistory(deployment_info=info_no_rev)

        await handler.execute([deployment])

        mock_deployment_executor.register_endpoints_bulk.assert_not_awaited()

    async def test_failed_registration_is_excluded_from_route_provisioning(
        self,
        handler: DeployingProvisioningHandler,
        mock_deployment_executor: AsyncMock,
        mock_evaluator: AsyncMock,
        deployment_created_without_revision: DeploymentWithHistory,
    ) -> None:
        """Failed registrations must not flow into this tick's route provisioning."""
        dep_id = deployment_created_without_revision.deployment_info.id
        mock_deployment_executor.register_endpoints_bulk.side_effect = None
        mock_deployment_executor.register_endpoints_bulk.return_value = DeploymentExecutionResult(
            failures=[
                DeploymentExecutionError(
                    deployment_info=deployment_created_without_revision,
                    reason="boom",
                    error_detail="Failed to register endpoint",
                )
            ],
        )

        await handler.execute([deployment_created_without_revision])

        evaluated_infos = mock_evaluator.evaluate.await_args.args[0]
        assert all(info.id != dep_id for info in evaluated_infos)
