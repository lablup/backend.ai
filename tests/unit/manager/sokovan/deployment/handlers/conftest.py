"""Fixtures for deploying handler tests."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

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
from ai.backend.manager.sokovan.deployment.types import DeploymentWithHistory


def _create_deploying_deployment_info(
    deployment_id: UUID | None = None,
    resource_group: str = "default",
    url: str | None = None,
    deploying_revision_id: UUID | None = None,
    current_revision_id: UUID | None = None,
) -> DeploymentInfo:
    """Create a DEPLOYING DeploymentInfo for tests."""
    dep_id = deployment_id or uuid4()
    deploying_rev_id = deploying_revision_id or uuid4()

    revision = MagicMock()
    revision.revision_id = deploying_rev_id

    return DeploymentInfo(
        id=dep_id,
        metadata=DeploymentMetadata(
            name="test-deployment",
            domain="default",
            project=uuid4(),
            resource_group=resource_group,
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
            url=url,
        ),
        model_revisions=[revision],
        current_revision_id=current_revision_id,
        deploying_revision_id=deploying_rev_id,
        sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
    )


@pytest.fixture
def mock_deployment_repo() -> AsyncMock:
    """Mock DeploymentRepository."""
    repo = AsyncMock()
    repo.fetch_scaling_group_proxy_targets = AsyncMock(return_value={})
    repo.update_endpoint_urls_bulk = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_deployment_executor() -> AsyncMock:
    """Mock DeploymentExecutor."""
    executor = AsyncMock()
    mock_revision_spec = MagicMock()
    mock_revision_spec.execution.runtime_variant = RuntimeVariant.CUSTOM
    executor.register_endpoint = AsyncMock(return_value="http://endpoint.test/v1")
    return executor


@pytest.fixture
def mock_deployment_controller() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_route_controller() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_evaluator() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_applier() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def deploying_provisioning_handler(
    mock_deployment_controller: AsyncMock,
    mock_route_controller: AsyncMock,
    mock_evaluator: AsyncMock,
    mock_applier: AsyncMock,
    mock_deployment_executor: AsyncMock,
    mock_deployment_repo: AsyncMock,
) -> DeployingProvisioningHandler:
    """Create DeployingProvisioningHandler with mocked dependencies."""
    return DeployingProvisioningHandler(
        deployment_controller=mock_deployment_controller,
        route_controller=mock_route_controller,
        evaluator=mock_evaluator,
        applier=mock_applier,
        deployment_executor=mock_deployment_executor,
        deployment_repo=mock_deployment_repo,
    )


@pytest.fixture
def proxy_target() -> ScalingGroupProxyTarget:
    return ScalingGroupProxyTarget(
        addr="http://proxy:8080",
        api_token="test-token",
    )


@pytest.fixture
def deploying_deployment_without_url() -> DeploymentWithHistory:
    """DEPLOYING deployment that has no URL (needs endpoint registration)."""
    return DeploymentWithHistory(
        deployment_info=_create_deploying_deployment_info(url=None),
    )


@pytest.fixture
def deploying_deployment_with_url() -> DeploymentWithHistory:
    """DEPLOYING deployment that already has a URL (skip registration)."""
    return DeploymentWithHistory(
        deployment_info=_create_deploying_deployment_info(url="http://already-registered/v1"),
    )
