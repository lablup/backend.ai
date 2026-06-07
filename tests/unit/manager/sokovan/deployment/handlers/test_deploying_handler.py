"""Tests for DeployingProvisioningHandler.

PROVISIONING no longer creates routes itself: the group scaling/rolling reconcile fills
routes and steps counts. This handler only polls the target replica group's lifecycle and
hands off to PROMOTING once it reaches STABLE.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    DeploymentMetadata,
    DeploymentNetworkData,
    DeploymentOptions,
    DeploymentState,
    ReplicaData,
    ReplicaGroupLifecycle,
)
from ai.backend.manager.sokovan.deployment.handlers.deploying_provisioning import (
    DeployingProvisioningHandler,
)
from ai.backend.manager.sokovan.deployment.types import DeploymentWithHistory
from ai.backend.manager.views.replica_group import ReplicaGroupDeploySchedulingView


class TestDeployingProvisioningHandler:
    """Tests for DeployingProvisioningHandler (wait for the target group to reach STABLE)."""

    @pytest.fixture
    def deploying_revision_id(self) -> DeploymentRevisionID:
        return DeploymentRevisionID(uuid4())

    @pytest.fixture
    def deployment(self, deploying_revision_id: DeploymentRevisionID) -> DeploymentWithHistory:
        return DeploymentWithHistory(
            deployment_info=DeploymentInfo(
                id=DeploymentID(uuid4()),
                primary_replica_group_id=ReplicaGroupID(uuid4()),
                target_replica_group_id=ReplicaGroupID(uuid4()),
                deploying_revision_id=deploying_revision_id,
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
                    scaling_state=ScalingState.STABLE,
                    retry_count=0,
                ),
                replica=ReplicaData(replica_count=1, desired_replica_count=1),
                network=DeploymentNetworkData(
                    open_to_public=False,
                    access_token_ids=None,
                    url="http://registered/v1",
                    preferred_domain_name=None,
                ),
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
                options=DeploymentOptions(),
            ),
            last_history=None,
        )

    @pytest.fixture
    def mock_replica_group_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_replica_group_repository: AsyncMock) -> DeployingProvisioningHandler:
        return DeployingProvisioningHandler(
            deployment_controller=AsyncMock(),
            replica_group_repository=mock_replica_group_repository,
        )

    @staticmethod
    def _target_group(
        deployment: DeploymentWithHistory,
        lifecycle: ReplicaGroupLifecycle,
    ) -> ReplicaGroupDeploySchedulingView:
        info = deployment.deployment_info
        assert info.target_replica_group_id is not None
        return ReplicaGroupDeploySchedulingView(
            group_id=info.target_replica_group_id,
            deployment_id=info.id,
            current_revision_id=None,
            target_revision_id=info.deploying_revision_id,
            lifecycle=lifecycle,
            traffic_weight=100,
        )

    async def test_target_group_stable_succeeds(
        self,
        handler: DeployingProvisioningHandler,
        mock_replica_group_repository: AsyncMock,
        deployment: DeploymentWithHistory,
    ) -> None:
        mock_replica_group_repository.search_deploy_scheduling_views.return_value = [
            self._target_group(deployment, ReplicaGroupLifecycle.STABLE)
        ]

        result = await handler.execute([deployment])

        assert [d.deployment_info.id for d in result.successes] == [deployment.deployment_info.id]
        assert not result.skipped
        assert not result.failures

    async def test_target_group_rolling_is_skipped(
        self,
        handler: DeployingProvisioningHandler,
        mock_replica_group_repository: AsyncMock,
        deployment: DeploymentWithHistory,
    ) -> None:
        mock_replica_group_repository.search_deploy_scheduling_views.return_value = [
            self._target_group(deployment, ReplicaGroupLifecycle.ROLLING)
        ]

        result = await handler.execute([deployment])

        assert [d.deployment_info.id for d in result.skipped] == [deployment.deployment_info.id]
        assert not result.successes
        assert not result.failures

    async def test_target_group_failed_is_failure(
        self,
        handler: DeployingProvisioningHandler,
        mock_replica_group_repository: AsyncMock,
        deployment: DeploymentWithHistory,
    ) -> None:
        mock_replica_group_repository.search_deploy_scheduling_views.return_value = [
            self._target_group(deployment, ReplicaGroupLifecycle.FAILED)
        ]

        result = await handler.execute([deployment])

        assert [e.deployment_info.deployment_info.id for e in result.failures] == [
            deployment.deployment_info.id
        ]
        assert not result.successes
        assert not result.skipped

    async def test_missing_target_group_is_skipped(
        self,
        handler: DeployingProvisioningHandler,
        mock_replica_group_repository: AsyncMock,
        deployment: DeploymentWithHistory,
    ) -> None:
        # INITIALIZING has not stamped the target revision on a group yet.
        mock_replica_group_repository.search_deploy_scheduling_views.return_value = []

        result = await handler.execute([deployment])

        assert [d.deployment_info.id for d in result.skipped] == [deployment.deployment_info.id]
        assert not result.successes
        assert not result.failures

    def test_success_transition_targets_promoting(self) -> None:
        transitions = DeployingProvisioningHandler.status_transitions()

        assert transitions.success is not None
        assert transitions.success.lifecycle == EndpointLifecycle.DEPLOYING
        assert transitions.success.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROMOTING

    def test_give_up_transition_targets_rolling_back(self) -> None:
        transitions = DeployingProvisioningHandler.status_transitions()

        assert transitions.give_up is not None
        assert transitions.give_up.lifecycle == EndpointLifecycle.DEPLOYING
        assert transitions.give_up.sub_step == DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK
