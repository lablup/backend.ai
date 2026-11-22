"""Unit tests for NodeShapeValidator."""

from __future__ import annotations

import pytest

from ai.backend.manager.sokovan.scheduler.provisioner.validators.exceptions import (
    NoNodeShapeFits,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.node_shape import (
    NodeShapeValidator,
)

from .conftest import SnapshotFactory, WorkloadFactory

_SHAPES = [
    {"cpu": "8", "mem": "32768"},
    {"cpu": "32", "mem": "131072", "cuda.shares": "4"},
]


@pytest.fixture
def validator() -> NodeShapeValidator:
    return NodeShapeValidator()


class TestNodeShapeValidator:
    def test_a_group_without_shapes_is_not_checked(
        self,
        validator: NodeShapeValidator,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        """A Docker group (and a kubernetes group whose cluster reported nothing) carries no
        shapes, so even a request larger than any node passes."""
        workload = workload_factory(slots={"cpu": "1000", "mem": "1"})

        validator.validate(snapshot_factory(), workload)

    def test_a_kernel_fitting_one_shape_passes(
        self,
        validator: NodeShapeValidator,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "16", "mem": "65536", "cuda.shares": "2"})

        validator.validate(snapshot_factory(node_shapes=_SHAPES), workload)

    def test_a_kernel_larger_than_every_shape_is_rejected(
        self,
        validator: NodeShapeValidator,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "64", "mem": "1024"})

        with pytest.raises(NoNodeShapeFits, match="cpu=64"):
            validator.validate(snapshot_factory(node_shapes=_SHAPES), workload)

    def test_the_request_must_fit_one_shape_not_the_union(
        self,
        validator: NodeShapeValidator,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        """cpu fits the first shape and mem the second, but no single node holds both."""
        shapes = [{"cpu": "32", "mem": "1024"}, {"cpu": "2", "mem": "131072"}]
        workload = workload_factory(slots={"cpu": "16", "mem": "65536"})

        with pytest.raises(NoNodeShapeFits):
            validator.validate(snapshot_factory(node_shapes=shapes), workload)

    def test_a_slot_no_node_has_is_rejected(
        self,
        validator: NodeShapeValidator,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "1", "mem": "1024", "atom.device": "1"})

        with pytest.raises(NoNodeShapeFits, match=r"atom\.device"):
            validator.validate(snapshot_factory(node_shapes=_SHAPES), workload)

    def test_zero_requests_are_ignored(
        self,
        validator: NodeShapeValidator,
        snapshot_factory: SnapshotFactory,
        workload_factory: WorkloadFactory,
    ) -> None:
        workload = workload_factory(slots={"cpu": "1", "mem": "1024", "atom.device": "0"})

        validator.validate(snapshot_factory(node_shapes=_SHAPES), workload)
