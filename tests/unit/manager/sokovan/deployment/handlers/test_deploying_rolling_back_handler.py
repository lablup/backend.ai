from __future__ import annotations

from datetime import datetime
from typing import cast
from unittest.mock import AsyncMock, MagicMock
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
    ModelRevisionData,
    ReplicaData,
)
from ai.backend.manager.sokovan.deployment.handlers.deploying_rolling_back import (
    DeployingRollingBackHandler,
)
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentWithHistory,
)


def _build_deployment(
    *,
    has_current_revision: bool,
) -> DeploymentWithHistory:
    current_revision: ModelRevisionData | None = None
    if has_current_revision:
        current_mock = MagicMock()
        current_mock.id = DeploymentRevisionID(uuid4())
        current_revision = cast(ModelRevisionData, current_mock)

    deploying_mock = MagicMock()
    deploying_mock.id = DeploymentRevisionID(uuid4())

    return DeploymentWithHistory(
        deployment_info=DeploymentInfo(
            primary_replica_group_id=ReplicaGroupID(uuid4()),
            id=DeploymentID(uuid4()),
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
            replica=ReplicaData(
                replica_count=1,
                desired_replica_count=1,
            ),
            network=DeploymentNetworkData(
                open_to_public=False,
                access_token_ids=None,
                url="http://endpoint/v1",
                preferred_domain_name=None,
            ),
            current_revision=current_revision,
            deploying_revision=cast(ModelRevisionData, deploying_mock),
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK,
            options=DeploymentOptions(),
        ),
        last_history=None,
    )


class TestDeployingRollingBackHandler:
    """Tests for DeployingRollingBackHandler."""

    @pytest.fixture
    def mock_deployment_repo(self) -> AsyncMock:
        repo = AsyncMock()
        repo.clear_deploying_revision = AsyncMock()
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_deployment_repo: AsyncMock,
    ) -> DeployingRollingBackHandler:
        return DeployingRollingBackHandler(
            deployment_controller=AsyncMock(),
            route_controller=AsyncMock(),
            deployment_repo=mock_deployment_repo,
        )

    async def test_with_current_revision_clears_and_marks_success(
        self,
        handler: DeployingRollingBackHandler,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        deployment = _build_deployment(has_current_revision=True)

        result = await handler.execute([deployment])

        assert len(result.successes) == 1
        assert result.successes[0] is deployment
        assert result.failures == []
        mock_deployment_repo.clear_deploying_revision.assert_awaited_once_with({
            deployment.deployment_info.id
        })

    async def test_without_current_revision_is_failure(
        self,
        handler: DeployingRollingBackHandler,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        deployment = _build_deployment(has_current_revision=False)

        result = await handler.execute([deployment])

        assert result.successes == []
        assert len(result.failures) == 1
        assert result.failures[0].deployment_info is deployment
        mock_deployment_repo.clear_deploying_revision.assert_not_awaited()

    async def test_mixed_batch_separates_successes_and_failures(
        self,
        handler: DeployingRollingBackHandler,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        with_revision = _build_deployment(has_current_revision=True)
        without_revision = _build_deployment(has_current_revision=False)

        result = await handler.execute([with_revision, without_revision])

        assert [d.deployment_info.id for d in result.successes] == [
            with_revision.deployment_info.id
        ]
        assert [e.deployment_info.deployment_info.id for e in result.failures] == [
            without_revision.deployment_info.id
        ]
        mock_deployment_repo.clear_deploying_revision.assert_awaited_once_with({
            with_revision.deployment_info.id
        })

    def test_status_transitions_route_failures_to_destroying(self) -> None:
        transitions = DeployingRollingBackHandler.status_transitions()

        assert transitions.success is not None
        assert transitions.success.lifecycle == EndpointLifecycle.READY
        for failure_transition in (
            transitions.need_retry,
            transitions.expired,
            transitions.give_up,
        ):
            assert failure_transition is not None
            assert failure_transition.lifecycle == EndpointLifecycle.DESTROYING
