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
from ai.backend.common.types import ClusterMode, ResourceSlot
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    DeploymentOptions,
    ExecutionData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    PresetAttributionData,
    ResourceConfigData,
)
from ai.backend.manager.models.endpoint.row import EndpointRow

RevisionFactory = Callable[[DeploymentRevisionID], Any]
EndpointFactory = Callable[..., Any]


@pytest.fixture
def revision_factory() -> RevisionFactory:
    """Build a ``DeploymentRevisionRow`` stub whose ``to_data()`` returns a
    minimal, well-formed ``ModelRevisionData``.
    """

    def _build(rev_id: DeploymentRevisionID) -> Any:
        rev = MagicMock()
        rev.id = rev_id
        rev.to_data.return_value = ModelRevisionData(
            id=rev_id,
            deployment_id=DeploymentID(uuid.uuid4()),
            revision_number=1,
            cluster_config=ClusterConfigData(mode=ClusterMode.SINGLE_NODE, size=1),
            resource_config=ResourceConfigData(
                resource_group_name="default",
                resource_slot=ResourceSlot({}),
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant_id=uuid.uuid4(),  # type: ignore[arg-type]
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=None,
                mount_destination="/models",
                definition_path="model-definition.yml",
                extra_mounts=[],
            ),
            execution=ExecutionData(
                startup_command=None,
                bootstrap_script=None,
                callback_url=None,
            ),
            preset=PresetAttributionData(preset_id=None, values=[]),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            image_id=None,
        )
        return rev

    return _build


@pytest.fixture
def endpoint_factory() -> EndpointFactory:
    """Build a non-DB stub that satisfies the projection method's reads.

    The projection is pure — instantiating a real ``EndpointRow`` against
    the DB schema would force a session and cascade test setup that has
    nothing to do with the projection logic, so a ``MagicMock`` carrying
    the columns the method touches is sufficient. The method is invoked
    unbound (``EndpointRow.to_model_deployment_data(stub)``) so the stub
    drives every attribute read.

    ``current_revision_row`` / ``deploying_revision_row`` mirror the
    BA-6056 relationship split on ``EndpointRow``; the method reads them
    directly so the stub exposes the same surface.
    """

    def _build(
        *,
        current_revision: DeploymentRevisionID | None = None,
        deploying_revision: DeploymentRevisionID | None = None,
        current_revision_row: Any = None,
        deploying_revision_row: Any = None,
        lifecycle_stage: EndpointLifecycle = EndpointLifecycle.DEPLOYING,
    ) -> Any:
        stub = MagicMock()
        stub.id = DeploymentID(uuid.uuid4())
        stub.name = "test-deployment"
        stub.lifecycle_stage = lifecycle_stage
        stub.tag = None
        stub.project = uuid.uuid4()
        stub.domain = "default"
        stub.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        stub.open_to_public = False
        stub.url = None
        stub.current_revision = current_revision
        stub.deploying_revision = deploying_revision
        stub.current_revision_row = current_revision_row
        stub.deploying_revision_row = deploying_revision_row
        stub.replicas = 1
        stub.desired_replicas = None
        stub.deployment_policy = None
        stub.created_user = uuid.uuid4()
        stub.options = DeploymentOptions()
        stub.scaling_state = ScalingState.STABLE
        stub.sub_step = None
        return stub

    return _build


class TestEndpointRowToDeploymentData:
    """Pin the API-facing projection to direct DB columns (BA-5979).

    The projection sources its current-revision spec from the
    ``current_revision_row`` relationship rather than scanning the
    ``revisions`` list — the original BA-5963 regression (a list-order
    swap between current and deploying) is structurally impossible
    once the lookup runs through a typed relationship instead of a
    list scan. These tests pin the new behavior: the spec follows the
    relationship, and the ID columns surface even when the row is
    absent (dangling reference).
    """

    def test_current_revision_resolved_via_current_revision_row(
        self,
        endpoint_factory: EndpointFactory,
        revision_factory: RevisionFactory,
    ) -> None:
        """The projection reads ``current_revision_row.to_data()`` directly."""
        current_id = DeploymentRevisionID(uuid.uuid4())
        deploying_id = DeploymentRevisionID(uuid.uuid4())
        endpoint = endpoint_factory(
            current_revision=current_id,
            deploying_revision=deploying_id,
            current_revision_row=revision_factory(current_id),
            deploying_revision_row=revision_factory(deploying_id),
        )

        data = EndpointRow.to_model_deployment_data(endpoint)

        assert data.current_revision_id == current_id
        assert data.deploying_revision_id == deploying_id
        assert data.current_revision_id != data.deploying_revision_id
        assert data.revision is not None
        assert data.revision.id == current_id

    def test_current_revision_id_survives_dangling_reference(
        self,
        endpoint_factory: EndpointFactory,
    ) -> None:
        """If the revision row was deleted but the column still points to it,
        surface the column ID and report the spec as ``None`` — do not collapse
        ``current_revision_id`` to ``None`` together with the missing spec.
        """
        dangling_id = DeploymentRevisionID(uuid.uuid4())

        endpoint = endpoint_factory(current_revision=dangling_id)

        data = EndpointRow.to_model_deployment_data(endpoint)

        assert data.current_revision_id == dangling_id
        assert data.deploying_revision_id is None
        assert data.revision is None

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
