"""Tests for the DEPLOYING provisioning/provisioned handlers.

PROVISIONING sets up the target replica group (action only); PROVISIONED waits for that group
to reach STABLE before handing off to PROMOTING.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.types import IntOrPercent
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    DeploymentMetadata,
    DeploymentNetworkData,
    DeploymentOptions,
    DeploymentPolicyData,
    DeploymentState,
    ReplicaData,
    ReplicaGroupLifecycle,
)
from ai.backend.manager.models.deployment_policy import RollingUpdateSpec
from ai.backend.manager.sokovan.deployment.handlers.deploying_provisioned import (
    DeployingProvisionedHandler,
)
from ai.backend.manager.sokovan.deployment.handlers.deploying_provisioning import (
    DeployingProvisioningHandler,
)
from ai.backend.manager.sokovan.deployment.types import DeploymentWithHistory
from ai.backend.manager.views.replica_group import ReplicaGroupDeploySchedulingView


def _make_deployment(
    *,
    sub_step: DeploymentLifecycleSubStep,
    target_replica_group_id: ReplicaGroupID | None,
    policy: DeploymentPolicyData | None = None,
) -> DeploymentWithHistory:
    return DeploymentWithHistory(
        deployment_info=DeploymentInfo(
            id=DeploymentID(uuid4()),
            primary_replica_group_id=ReplicaGroupID(uuid4()),
            target_replica_group_id=target_replica_group_id,
            deploying_revision_id=DeploymentRevisionID(uuid4()),
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
            sub_step=sub_step,
            options=DeploymentOptions(),
            policy=policy,
        ),
        last_history=None,
    )


def _rolling_policy() -> DeploymentPolicyData:
    return DeploymentPolicyData(
        id=uuid4(),
        endpoint=uuid4(),
        strategy=DeploymentStrategy.ROLLING,
        strategy_spec=RollingUpdateSpec(
            max_surge=IntOrPercent(count=1),
            max_unavailable=IntOrPercent(count=0),
        ),
        created_at=datetime.now(tzutc()),
        updated_at=datetime.now(tzutc()),
    )


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


class TestDeployingProvisioningHandler:
    """PROVISIONING sets up the target replica group, then hands off to PROVISIONED."""

    @pytest.fixture
    def mock_replica_group_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_replica_group_repository: AsyncMock) -> DeployingProvisioningHandler:
        return DeployingProvisioningHandler(
            deployment_controller=AsyncMock(),
            replica_group_repository=mock_replica_group_repository,
        )

    async def test_rolling_sets_up_reusing_primary(
        self,
        handler: DeployingProvisioningHandler,
        mock_replica_group_repository: AsyncMock,
    ) -> None:
        deployment = _make_deployment(
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
            target_replica_group_id=None,
            policy=_rolling_policy(),
        )
        info = deployment.deployment_info
        mock_replica_group_repository.setup_target_groups.return_value = {info.id}

        result = await handler.execute([deployment])

        mock_replica_group_repository.setup_target_groups.assert_awaited_once()
        setups = mock_replica_group_repository.setup_target_groups.await_args.args[0]
        # Rolling reuses the primary group; the setup resolves it at creation time.
        assert [setup.spec.use_primary_group for setup in setups] == [True]
        assert [d.deployment_info.id for d in result.successes] == [info.id]
        assert not result.failures

    async def test_setup_not_applied_is_failure(
        self,
        handler: DeployingProvisioningHandler,
        mock_replica_group_repository: AsyncMock,
    ) -> None:
        deployment = _make_deployment(
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
            target_replica_group_id=None,
            policy=_rolling_policy(),
        )
        mock_replica_group_repository.setup_target_groups.return_value = set()

        result = await handler.execute([deployment])

        assert [e.deployment_info.deployment_info.id for e in result.failures] == [
            deployment.deployment_info.id
        ]
        assert not result.successes

    async def test_no_policy_is_failure(
        self,
        handler: DeployingProvisioningHandler,
        mock_replica_group_repository: AsyncMock,
    ) -> None:
        deployment = _make_deployment(
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
            target_replica_group_id=None,
            policy=None,
        )

        result = await handler.execute([deployment])

        mock_replica_group_repository.setup_target_groups.assert_not_called()
        assert [e.deployment_info.deployment_info.id for e in result.failures] == [
            deployment.deployment_info.id
        ]
        assert not result.successes

    def test_success_transition_targets_provisioned(self) -> None:
        transitions = DeployingProvisioningHandler.status_transitions()
        assert transitions.success is not None
        assert transitions.success.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONED

    def test_give_up_transition_targets_rolling_back(self) -> None:
        transitions = DeployingProvisioningHandler.status_transitions()
        assert transitions.give_up is not None
        assert transitions.give_up.sub_step == DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK


class TestDeployingProvisionedHandler:
    """PROVISIONED waits for the target group to reach STABLE before promoting."""

    @pytest.fixture
    def mock_replica_group_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_replica_group_repository: AsyncMock) -> DeployingProvisionedHandler:
        return DeployingProvisionedHandler(
            deployment_controller=AsyncMock(),
            replica_group_repository=mock_replica_group_repository,
        )

    @pytest.fixture
    def deployment(self) -> DeploymentWithHistory:
        return _make_deployment(
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONED,
            target_replica_group_id=ReplicaGroupID(uuid4()),
        )

    async def test_target_group_stable_succeeds(
        self,
        handler: DeployingProvisionedHandler,
        mock_replica_group_repository: AsyncMock,
        deployment: DeploymentWithHistory,
    ) -> None:
        mock_replica_group_repository.search_deploy_scheduling_views.return_value = [
            _target_group(deployment, ReplicaGroupLifecycle.STABLE)
        ]

        result = await handler.execute([deployment])

        assert [d.deployment_info.id for d in result.successes] == [deployment.deployment_info.id]
        assert not result.skipped
        assert not result.failures

    async def test_target_group_rolling_is_failure(
        self,
        handler: DeployingProvisionedHandler,
        mock_replica_group_repository: AsyncMock,
        deployment: DeploymentWithHistory,
    ) -> None:
        # Still rolling out: report a failure so the coordinator keeps the
        # deployment waiting (NEED_RETRY) and the phase timeout can eventually
        # expire into rollback — never a skip (skips leave no history).
        mock_replica_group_repository.search_deploy_scheduling_views.return_value = [
            _target_group(deployment, ReplicaGroupLifecycle.ROLLING)
        ]

        result = await handler.execute([deployment])

        assert [e.deployment_info.deployment_info.id for e in result.failures] == [
            deployment.deployment_info.id
        ]
        assert not result.successes
        assert not result.skipped

    async def test_target_group_failed_is_failure(
        self,
        handler: DeployingProvisionedHandler,
        mock_replica_group_repository: AsyncMock,
        deployment: DeploymentWithHistory,
    ) -> None:
        mock_replica_group_repository.search_deploy_scheduling_views.return_value = [
            _target_group(deployment, ReplicaGroupLifecycle.FAILED)
        ]

        result = await handler.execute([deployment])

        assert [e.deployment_info.deployment_info.id for e in result.failures] == [
            deployment.deployment_info.id
        ]
        assert not result.successes
        assert not result.skipped

    async def test_target_group_drained_is_failure(
        self,
        handler: DeployingProvisionedHandler,
        mock_replica_group_repository: AsyncMock,
        deployment: DeploymentWithHistory,
    ) -> None:
        mock_replica_group_repository.search_deploy_scheduling_views.return_value = [
            _target_group(deployment, ReplicaGroupLifecycle.DRAINED)
        ]

        result = await handler.execute([deployment])

        assert [e.deployment_info.deployment_info.id for e in result.failures] == [
            deployment.deployment_info.id
        ]
        assert not result.successes
        assert not result.skipped

    async def test_missing_target_group_is_failure(
        self,
        handler: DeployingProvisionedHandler,
        mock_replica_group_repository: AsyncMock,
        deployment: DeploymentWithHistory,
    ) -> None:
        mock_replica_group_repository.search_deploy_scheduling_views.return_value = []

        result = await handler.execute([deployment])

        assert [e.deployment_info.deployment_info.id for e in result.failures] == [
            deployment.deployment_info.id
        ]
        assert not result.successes
        assert not result.skipped

    def test_success_transition_targets_promoting(self) -> None:
        transitions = DeployingProvisionedHandler.status_transitions()
        assert transitions.success is not None
        assert transitions.success.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROMOTING

    def test_give_up_transition_targets_rolling_back(self) -> None:
        transitions = DeployingProvisionedHandler.status_transitions()
        assert transitions.give_up is not None
        assert transitions.give_up.sub_step == DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK
