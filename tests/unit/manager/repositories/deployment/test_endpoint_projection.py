"""Tests for the API-facing ``EndpointRow`` projection at the repository boundary."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.data.model_deployment.types import ModelDeploymentStatus
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.manager.data.deployment.types import DeploymentOptions
from ai.backend.manager.models.endpoint.row import EndpointRow

EndpointFactory = Callable[..., Any]


@pytest.fixture
def endpoint_factory() -> EndpointFactory:
    """Build a non-DB stub that satisfies the projection method's reads.

    The projection is pure and reads only the endpoint row's own columns —
    no relationship access — so a ``MagicMock`` carrying the columns the
    method touches is sufficient. The mock is bound to ``spec=EndpointRow``
    so a column the projection reads that no longer exists on the row
    (e.g. renamed/removed) raises ``AttributeError`` instead of silently
    fabricating a value. ``EndpointRow.to_model_deployment_data`` is invoked
    unbound so the stub drives every attribute read.
    """

    def _build(
        *,
        current_revision: DeploymentRevisionID | None = None,
        deploying_revision: DeploymentRevisionID | None = None,
        lifecycle_stage: EndpointLifecycle = EndpointLifecycle.DEPLOYING,
    ) -> Any:
        stub = MagicMock(spec=EndpointRow)
        stub.id = DeploymentID(uuid.uuid4())
        stub.name = "test-deployment"
        stub.lifecycle_stage = lifecycle_stage
        stub.tag = None
        stub.project = uuid.uuid4()
        stub.domain = "default"
        stub.resource_group = "default"
        stub.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        stub.open_to_public = False
        stub.url = None
        stub.current_revision = current_revision
        stub.deploying_revision = deploying_revision
        stub.replicas = 1
        stub.desired_replicas = None
        stub.created_user = uuid.uuid4()
        stub.options = DeploymentOptions()
        stub.scaling_state = ScalingState.STABLE
        stub.sub_step = None
        return stub

    return _build


class TestEndpointRowToDeploymentData:
    """Pin the API-facing projection to direct DB columns (BA-5979).

    The projection only surfaces scope IDs from the row's own columns —
    revision specs and policy are fetched by callers (GQL DataLoaders or
    nested REST endpoints), not joined here. These tests pin the column
    pass-through and the lifecycle → status mapping.
    """

    def test_revision_ids_surface_from_columns(
        self,
        endpoint_factory: EndpointFactory,
    ) -> None:
        """``current_revision`` / ``deploying_revision`` columns flow through
        as-is — no joined ``revision`` spec is included in the projection.
        """
        current_id = DeploymentRevisionID(uuid.uuid4())
        deploying_id = DeploymentRevisionID(uuid.uuid4())
        endpoint = endpoint_factory(
            current_revision=current_id,
            deploying_revision=deploying_id,
        )

        data = EndpointRow.to_model_deployment_data(endpoint)

        assert data.current_revision_id == current_id
        assert data.deploying_revision_id == deploying_id

    def test_null_revision_ids_surface_as_none(
        self,
        endpoint_factory: EndpointFactory,
    ) -> None:
        endpoint = endpoint_factory()

        data = EndpointRow.to_model_deployment_data(endpoint)

        assert data.current_revision_id is None
        assert data.deploying_revision_id is None

    @pytest.mark.parametrize(
        ("lifecycle", "expected_status"),
        [
            (EndpointLifecycle.PENDING, ModelDeploymentStatus.PENDING),
            (EndpointLifecycle.CREATED, ModelDeploymentStatus.PENDING),
            (EndpointLifecycle.READY, ModelDeploymentStatus.READY),
            (EndpointLifecycle.SCALING, ModelDeploymentStatus.READY),
            (EndpointLifecycle.DEPLOYING, ModelDeploymentStatus.DEPLOYING),
            (EndpointLifecycle.DESTROYING, ModelDeploymentStatus.STOPPING),
            (EndpointLifecycle.DESTROYED, ModelDeploymentStatus.STOPPED),
        ],
        ids=[
            "pending",
            "created",
            "ready",
            "scaling",
            "deploying",
            "destroying",
            "destroyed",
        ],
    )
    def test_lifecycle_status_mapping(
        self,
        endpoint_factory: EndpointFactory,
        lifecycle: EndpointLifecycle,
        expected_status: ModelDeploymentStatus,
    ) -> None:
        """Status surface follows the lifecycle column directly."""
        endpoint = endpoint_factory(lifecycle_stage=lifecycle)

        data = EndpointRow.to_model_deployment_data(endpoint)

        assert data.metadata.status == expected_status
