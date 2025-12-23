"""Tests for ClusterConfigurationRule."""

from unittest.mock import MagicMock

import pytest

from ai.backend.common.types import ClusterMode
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    ContainerUserInfo,
    SessionCreationContext,
    SessionCreationSpec,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.cluster import (
    ClusterConfigurationRule,
)


@pytest.fixture
def cluster_rule():
    """Create a ClusterConfigurationRule instance."""
    return ClusterConfigurationRule()


@pytest.fixture
def basic_context():
    """Create a basic SessionCreationContext."""
    return SessionCreationContext(
        scaling_group_network=None,
        allowed_scaling_groups=[],
        image_infos={},
        vfolder_mounts=[],
        dotfile_data={},
        container_user_info=ContainerUserInfo(),
    )


class TestClusterConfigurationRule:
    """Test cases for ClusterConfigurationRule."""

    def test_single_kernel_session(self, cluster_rule, basic_context):
        """Test single kernel session configuration."""
        spec = SessionCreationSpec(
            session_creation_id="test-001",
            session_name="single-kernel",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[{"image_ref": MagicMock(canonical="test-image")}],
            creation_spec={},
        )

        preparation_data = {}
        cluster_rule.prepare(spec, basic_context, preparation_data)

        kernel_configs = preparation_data["kernel_configs"]
        assert len(kernel_configs) == 1
        assert kernel_configs[0]["cluster_role"] == DEFAULT_ROLE

    def test_multi_container_single_spec_replication(self, cluster_rule, basic_context):
        """Test multi-container session with single kernel spec (replication mode)."""
        spec = SessionCreationSpec(
            session_creation_id="test-002",
            session_name="multi-container",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=4,
            priority=10,
            resource_policy={},
            kernel_specs=[{"image_ref": MagicMock(canonical="test-image")}],
            creation_spec={},
        )

        preparation_data = {}
        cluster_rule.prepare(spec, basic_context, preparation_data)

        kernel_configs = preparation_data["kernel_configs"]
        assert len(kernel_configs) == 4

        # Check main kernel
        assert kernel_configs[0]["cluster_role"] == "main"
        assert kernel_configs[0]["cluster_idx"] == 1
        assert kernel_configs[0]["local_rank"] == 0
        assert kernel_configs[0]["cluster_hostname"] == "main1"

        # Check sub kernels
        for i in range(1, 4):
            assert kernel_configs[i]["cluster_role"] == "sub"
            assert kernel_configs[i]["cluster_idx"] == i  # sub1: 1, sub2: 2, sub3: 3
            assert kernel_configs[i]["local_rank"] == i
            assert kernel_configs[i]["cluster_hostname"] == f"sub{i}"

    def test_multi_container_multiple_specs(self, cluster_rule, basic_context):
        """Test multi-container session with multiple kernel specs."""
        spec = SessionCreationSpec(
            session_creation_id="test-003",
            session_name="multi-spec",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=3,
            priority=10,
            resource_policy={},
            kernel_specs=[
                {"image_ref": MagicMock(canonical="image1")},
                {"image_ref": MagicMock(canonical="image2")},
                {"image_ref": MagicMock(canonical="image3")},
            ],
            creation_spec={},
        )

        preparation_data = {}
        cluster_rule.prepare(spec, basic_context, preparation_data)

        kernel_configs = preparation_data["kernel_configs"]
        assert len(kernel_configs) == 3

        # First kernel should be main
        assert kernel_configs[0]["cluster_role"] == DEFAULT_ROLE
        assert kernel_configs[0]["cluster_idx"] == 1
        assert kernel_configs[0]["cluster_hostname"] == f"{DEFAULT_ROLE}1"

        # Rest should be sub kernels
        assert kernel_configs[1]["cluster_role"] == "sub"
        assert kernel_configs[1]["cluster_idx"] == 1
        assert kernel_configs[1]["cluster_hostname"] == "sub1"

        assert kernel_configs[2]["cluster_role"] == "sub"
        assert kernel_configs[2]["cluster_idx"] == 2
        assert kernel_configs[2]["cluster_hostname"] == "sub2"

    def test_predefined_cluster_roles(self, cluster_rule, basic_context):
        """Test handling of predefined cluster roles in kernel specs."""
        spec = SessionCreationSpec(
            session_creation_id="test-004",
            session_name="predefined-roles",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=3,
            priority=10,
            resource_policy={},
            kernel_specs=[
                {
                    "image_ref": MagicMock(canonical="image1"),
                    "cluster_role": "main",
                    "cluster_idx": 1,
                },
                {
                    "image_ref": MagicMock(canonical="image2"),
                    "cluster_role": "sub",
                    "cluster_idx": 1,
                },
                {
                    "image_ref": MagicMock(canonical="image3"),
                    "cluster_role": "sub",
                    "cluster_idx": 2,
                },
            ],
            creation_spec={},
        )

        preparation_data = {}
        cluster_rule.prepare(spec, basic_context, preparation_data)

        kernel_configs = preparation_data["kernel_configs"]
        assert len(kernel_configs) == 3

        # Should preserve predefined roles
        assert kernel_configs[0]["cluster_role"] == "main"
        assert kernel_configs[0]["cluster_idx"] == 1
        assert kernel_configs[0]["cluster_hostname"] == "main1"

        assert kernel_configs[1]["cluster_role"] == "sub"
        assert kernel_configs[1]["cluster_idx"] == 1
        assert kernel_configs[1]["cluster_hostname"] == "sub1"

        assert kernel_configs[2]["cluster_role"] == "sub"
        assert kernel_configs[2]["cluster_idx"] == 2
        assert kernel_configs[2]["cluster_hostname"] == "sub2"

    def test_custom_cluster_hostnames(self, cluster_rule, basic_context):
        """Test preservation of custom cluster hostnames."""
        spec = SessionCreationSpec(
            session_creation_id="test-005",
            session_name="custom-hostnames",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=2,
            priority=10,
            resource_policy={},
            kernel_specs=[
                {"image_ref": MagicMock(canonical="image1"), "cluster_hostname": "master"},
                {"image_ref": MagicMock(canonical="image2"), "cluster_hostname": "worker1"},
            ],
            creation_spec={},
        )

        preparation_data = {}
        cluster_rule.prepare(spec, basic_context, preparation_data)

        kernel_configs = preparation_data["kernel_configs"]
        assert len(kernel_configs) == 2

        # Should preserve custom hostnames
        assert kernel_configs[0]["cluster_hostname"] == "master"
        assert kernel_configs[1]["cluster_hostname"] == "worker1"

    def test_mixed_predefined_and_auto_assignment(self, cluster_rule, basic_context):
        """Test mixed scenario with some predefined roles and some auto-assigned."""
        spec = SessionCreationSpec(
            session_creation_id="test-006",
            session_name="mixed-roles",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=4,
            priority=10,
            resource_policy={},
            kernel_specs=[
                {"image_ref": MagicMock(canonical="image1")},  # Should auto-assign as main
                {
                    "image_ref": MagicMock(canonical="image2"),
                    "cluster_role": "sub",
                },  # Predefined sub
                {"image_ref": MagicMock(canonical="image3")},  # Should auto-assign as sub
                {
                    "image_ref": MagicMock(canonical="image4"),
                    "cluster_role": "sub",
                    "cluster_idx": 5,
                },  # Predefined sub with custom idx
            ],
            creation_spec={},
        )

        preparation_data = {}
        cluster_rule.prepare(spec, basic_context, preparation_data)

        kernel_configs = preparation_data["kernel_configs"]
        assert len(kernel_configs) == 4

        # First kernel auto-assigned as main
        assert kernel_configs[0]["cluster_role"] == DEFAULT_ROLE
        assert kernel_configs[0]["cluster_idx"] == 1

        # Second kernel with predefined sub role
        assert kernel_configs[1]["cluster_role"] == "sub"
        assert kernel_configs[1]["cluster_idx"] == 1  # First sub

        # Third kernel auto-assigned as sub
        assert kernel_configs[2]["cluster_role"] == "sub"
        assert kernel_configs[2]["cluster_idx"] == 2  # Second sub

        # Fourth kernel with predefined sub role and custom idx
        assert kernel_configs[3]["cluster_role"] == "sub"
        assert kernel_configs[3]["cluster_idx"] == 5  # Custom idx preserved

    def test_large_cluster(self, cluster_rule, basic_context):
        """Test large cluster configuration."""
        cluster_size = 10
        spec = SessionCreationSpec(
            session_creation_id="test-007",
            session_name="large-cluster",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=ClusterMode.MULTI_NODE,
            cluster_size=cluster_size,
            priority=10,
            resource_policy={},
            kernel_specs=[
                {"image_ref": MagicMock(canonical="test-image")}
            ],  # Single spec to replicate
            creation_spec={},
        )

        preparation_data = {}
        cluster_rule.prepare(spec, basic_context, preparation_data)

        kernel_configs = preparation_data["kernel_configs"]
        assert len(kernel_configs) == cluster_size

        # Verify all sub kernels have correct indices
        for i in range(1, cluster_size):
            assert kernel_configs[i]["cluster_role"] == "sub"
            assert kernel_configs[i]["cluster_idx"] == i
            assert kernel_configs[i]["local_rank"] == i
            assert kernel_configs[i]["cluster_hostname"] == f"sub{i}"
