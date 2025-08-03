"""Test resource requirements and aggregation logic."""

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.selectors.selector import (
    AgentSelectionCriteria2,
    ResourceRequirements,
    SessionMetadata,
)


class TestResourceRequirements:
    """Test ResourceRequirements functionality."""

    def test_single_node_aggregation(self):
        """Test that single-node sessions aggregate resource requirements."""
        # Create session metadata for single-node
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INTERACTIVE,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        # Create kernel requirements with same architecture
        kernel_reqs = {
            uuid.uuid4(): ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("1"),
                    "mem": Decimal("2048"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("3"),
                    "mem": Decimal("8192"),
                }),
                required_architecture="x86_64",
            ),
        }

        criteria = AgentSelectionCriteria2(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        # Get aggregated requirements
        resource_reqs = criteria.get_resource_requirements()

        # Should return single aggregated requirement
        assert len(resource_reqs) == 1

        # Check aggregated values
        agg_req = resource_reqs[0]
        assert agg_req.requested_slots["cpu"] == Decimal("6")  # 2+1+3
        assert agg_req.requested_slots["mem"] == Decimal("14336")  # 4096+2048+8192
        assert agg_req.required_architecture == "x86_64"

    def test_single_node_mixed_architecture_error(self):
        """Test that single-node sessions with mixed architectures raise error."""
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.BATCH,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        # Create kernel requirements with different architectures
        kernel_reqs = {
            uuid.uuid4(): ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("1"),
                    "mem": Decimal("2048"),
                }),
                required_architecture="aarch64",  # Different architecture
            ),
        }

        criteria = AgentSelectionCriteria2(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            criteria.get_resource_requirements()

        assert "different architectures" in str(exc_info.value)

    def test_multi_node_individual_resources(self):
        """Test that multi-node sessions return individual kernel resources."""
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INTERACTIVE,
            scaling_group="default",
            cluster_mode=ClusterMode.MULTI_NODE,
        )

        # Create kernel requirements
        kernel_ids = [uuid.uuid4() for _ in range(3)]
        kernel_reqs = {
            kernel_ids[0]: ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                }),
                required_architecture="x86_64",
            ),
            kernel_ids[1]: ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("1"),
                    "mem": Decimal("2048"),
                }),
                required_architecture="x86_64",
            ),
            kernel_ids[2]: ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("3"),
                    "mem": Decimal("8192"),
                }),
                required_architecture="aarch64",  # Different architecture is OK for multi-node
            ),
        }

        criteria = AgentSelectionCriteria2(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        # Get resource requirements
        resource_reqs = criteria.get_resource_requirements()

        # Should return individual requirements
        assert len(resource_reqs) == 3

        # Convert to list for easier checking
        reqs_list = list(resource_reqs)

        # Verify each requirement matches original
        for req in reqs_list:
            # Find matching kernel requirement
            found = False
            for kernel_req in kernel_reqs.values():
                if (
                    req.requested_slots == kernel_req.requested_slots
                    and req.required_architecture == kernel_req.required_architecture
                ):
                    found = True
                    break
            assert found, f"Resource requirement {req} not found in kernel requirements"

    def test_empty_kernel_requirements(self):
        """Test handling of empty kernel requirements."""
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INFERENCE,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        criteria = AgentSelectionCriteria2(
            session_metadata=session_metadata,
            kernel_requirements={},  # Empty
        )

        # Get resource requirements
        resource_reqs = criteria.get_resource_requirements()

        # Should return single empty requirement with default architecture
        assert len(resource_reqs) == 1
        assert resource_reqs[0].requested_slots == ResourceSlot({})
        assert resource_reqs[0].required_architecture == "x86_64"

    def test_single_node_gpu_aggregation(self):
        """Test GPU resource aggregation for single-node sessions."""
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.BATCH,
            scaling_group="gpu-group",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        # Create kernel requirements with GPU resources
        kernel_reqs = {
            uuid.uuid4(): ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("4"),
                    "mem": Decimal("16384"),
                    "cuda.shares": Decimal("1"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): ResourceRequirements(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("8192"),
                    "cuda.shares": Decimal("0.5"),
                }),
                required_architecture="x86_64",
            ),
        }

        criteria = AgentSelectionCriteria2(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        # Get aggregated requirements
        resource_reqs = criteria.get_resource_requirements()

        # Check aggregated GPU resources
        assert len(resource_reqs) == 1
        agg_req = resource_reqs[0]
        assert agg_req.requested_slots["cpu"] == Decimal("6")
        assert agg_req.requested_slots["mem"] == Decimal("24576")
        assert agg_req.requested_slots["cuda.shares"] == Decimal("1.5")

    def test_resource_slot_addition(self):
        """Test that ResourceSlot addition works correctly."""
        slot1 = ResourceSlot({
            "cpu": Decimal("2"),
            "mem": Decimal("4096"),
            "cuda.shares": Decimal("1"),
        })

        slot2 = ResourceSlot({
            "cpu": Decimal("3"),
            "mem": Decimal("8192"),
            "cuda.shares": Decimal("2"),
            "special": Decimal("5"),  # Additional resource type
        })

        # Add slots
        result = slot1 + slot2

        # Check result
        assert result["cpu"] == Decimal("5")
        assert result["mem"] == Decimal("12288")
        assert result["cuda.shares"] == Decimal("3")
        assert result["special"] == Decimal("5")  # New resource type included
