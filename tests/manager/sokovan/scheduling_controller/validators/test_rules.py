"""Tests for validation rules."""

from unittest.mock import MagicMock

import pytest

from ai.backend.common.types import SessionTypes
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.kernel import QuotaExceeded
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    ContainerUserInfo,
    ImageInfo,
    SessionCreationContext,
    SessionCreationSpec,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.cluster import (
    ClusterValidationRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.rules import (
    ContainerLimitRule,
    ScalingGroupAccessRule,
    ServicePortRule,
)


@pytest.fixture
def basic_context():
    """Create a basic SessionCreationContext."""
    return SessionCreationContext(
        scaling_group_network=None,
        allowed_scaling_groups=[
            AllowedScalingGroup(
                name="public-sg", is_private=False, scheduler_opts=ScalingGroupOpts()
            ),
            AllowedScalingGroup(
                name="private-sg", is_private=True, scheduler_opts=ScalingGroupOpts()
            ),
        ],
        image_infos={
            "test-image": ImageInfo(
                canonical="test-image",
                architecture="x86_64",
                registry="localhost",
                labels={
                    "ai.backend.service-ports": "jupyter:http:8888,vscode:http:8080",
                },
                resource_spec={},
            )
        },
        vfolder_mounts=[],
        dotfile_data={},
        container_user_info=ContainerUserInfo(),
    )


class TestContainerLimitRule:
    """Test cases for ContainerLimitRule."""

    def test_within_limit(self, basic_context):
        """Test cluster size within limits."""
        rule = ContainerLimitRule()
        spec = SessionCreationSpec(
            session_creation_id="test-001",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=3,
            priority=10,
            resource_policy={"max_containers_per_session": 5},
            kernel_specs=[],
            creation_spec={},
        )

        # Should not raise
        rule.validate(spec, basic_context, [])

    def test_exceeds_limit(self, basic_context):
        """Test cluster size exceeding limits."""
        rule = ContainerLimitRule()
        spec = SessionCreationSpec(
            session_creation_id="test-002",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=10,
            priority=10,
            resource_policy={"max_containers_per_session": 5},
            kernel_specs=[],
            creation_spec={},
        )

        with pytest.raises(QuotaExceeded) as exc_info:
            rule.validate(spec, basic_context, [])
        assert "cannot create session with more than 5 containers" in str(exc_info.value)

    def test_default_limit(self, basic_context):
        """Test default limit when not specified."""
        rule = ContainerLimitRule()
        spec = SessionCreationSpec(
            session_creation_id="test-003",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=2,
            priority=10,
            resource_policy={},  # No limit specified, defaults to 1
            kernel_specs=[],
            creation_spec={},
        )

        with pytest.raises(QuotaExceeded):
            rule.validate(spec, basic_context, [])


class TestScalingGroupAccessRule:
    """Test cases for ScalingGroupAccessRule."""

    def test_public_session_public_sgroup(self, basic_context):
        """Test public session accessing public scaling group."""
        rule = ScalingGroupAccessRule()
        spec = SessionCreationSpec(
            session_creation_id="test-001",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,  # Public session type
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={},
            scaling_group="public-sg",
        )

        # Should not raise
        rule.validate(spec, basic_context, basic_context.allowed_scaling_groups)

    def test_public_session_private_sgroup(self, basic_context):
        """Test public session trying to access private scaling group."""
        rule = ScalingGroupAccessRule()
        spec = SessionCreationSpec(
            session_creation_id="test-002",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,  # Public session type
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={},
            scaling_group="private-sg",
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context, basic_context.allowed_scaling_groups)
        assert "not allowed for" in str(exc_info.value)

    def test_private_session_private_sgroup(self, basic_context):
        """Test private session accessing private scaling group."""
        rule = ScalingGroupAccessRule()
        # Assuming SYSTEM is a private session type
        spec = SessionCreationSpec(
            session_creation_id="test-003",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.SYSTEM,  # Private session type
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={},
            scaling_group="private-sg",
        )

        # Should not raise
        rule.validate(spec, basic_context, basic_context.allowed_scaling_groups)

    def test_inaccessible_sgroup(self, basic_context):
        """Test accessing non-existent scaling group."""
        rule = ScalingGroupAccessRule()
        spec = SessionCreationSpec(
            session_creation_id="test-004",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={},
            scaling_group="nonexistent-sg",
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context, basic_context.allowed_scaling_groups)
        assert "not accessible" in str(exc_info.value)


class TestServicePortRule:
    """Test cases for ServicePortRule."""

    def test_reserved_ports(self, basic_context):
        """Test validation of reserved ports."""
        rule = ServicePortRule()
        spec = SessionCreationSpec(
            session_creation_id="test-001",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[
                {
                    "image_ref": type("ImageRef", (), {"canonical": "test-image"})(),
                    "creation_config": {
                        "preopen_ports": [2000, 8080],  # 2000 is reserved
                    },
                }
            ],
            creation_spec={},
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context, [])
        assert "reserved for internal use" in str(exc_info.value)

    def test_service_port_overlap(self, basic_context):
        """Test validation of overlapping service ports."""
        rule = ServicePortRule()
        spec = SessionCreationSpec(
            session_creation_id="test-002",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[
                {
                    "image_ref": type("ImageRef", (), {"canonical": "test-image"})(),
                    "creation_config": {
                        "preopen_ports": [8888, 9000],  # 8888 overlaps with jupyter service port
                    },
                }
            ],
            creation_spec={},
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context, [])
        assert "overlap with service port" in str(exc_info.value)

    def test_creation_config_preopen_ports(self, basic_context):
        """Test validation of preopen_ports from creation_config."""
        rule = ServicePortRule()
        spec = SessionCreationSpec(
            session_creation_id="test-003",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[{"image_ref": type("ImageRef", (), {"canonical": "test-image"})()}],
            creation_spec={
                "preopen_ports": [2001, 3000],  # 2001 is reserved
            },
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context, [])
        assert "reserved for internal use" in str(exc_info.value)

    def test_valid_ports(self, basic_context):
        """Test validation with valid ports."""
        rule = ServicePortRule()
        spec = SessionCreationSpec(
            session_creation_id="test-004",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[
                {
                    "image_ref": type("ImageRef", (), {"canonical": "test-image"})(),
                    "creation_config": {
                        "preopen_ports": [3000, 4000, 5000],  # All valid ports
                    },
                }
            ],
            creation_spec={},
        )

        # Should not raise
        rule.validate(spec, basic_context, [])

    def test_all_reserved_ports(self, basic_context):
        """Test all reserved ports (2000, 2001, 2200, 7681)."""
        rule = ServicePortRule()
        reserved_ports = [2000, 2001, 2200, 7681]

        for port in reserved_ports:
            spec = SessionCreationSpec(
                session_creation_id=f"test-reserved-{port}",
                session_name="test",
                access_key="test-key",
                user_scope=None,
                session_type=SessionTypes.INTERACTIVE,
                cluster_mode=None,
                cluster_size=1,
                priority=10,
                resource_policy={},
                kernel_specs=[],
                creation_spec={
                    "preopen_ports": [port],
                },
            )

            with pytest.raises(InvalidAPIParameters) as exc_info:
                rule.validate(spec, basic_context, [])
            assert "reserved for internal use" in str(exc_info.value)


class TestClusterValidationRule:
    """Test cases for ClusterValidationRule."""

    def test_no_kernel_specs(self):
        """Test validation with no kernel specs."""
        rule = ClusterValidationRule()
        spec = SessionCreationSpec(
            session_creation_id="test-001",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],  # Empty kernel specs
            creation_spec={},
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, None, [])
        assert "at least one kernel specification" in str(exc_info.value).lower()

    def test_single_container(self):
        """Test validation for single container session."""
        rule = ClusterValidationRule()
        spec = SessionCreationSpec(
            session_creation_id="test-002",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[{"image_ref": MagicMock(canonical="test-image")}],
            creation_spec={},
        )

        # Should not raise for single container
        rule.validate(spec, None, [])

    def test_multi_container_single_spec(self):
        """Test multi-container with single kernel spec (valid for replication)."""
        rule = ClusterValidationRule()
        spec = SessionCreationSpec(
            session_creation_id="test-003",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=4,
            priority=10,
            resource_policy={},
            kernel_specs=[
                {"image_ref": MagicMock(canonical="test-image")}
            ],  # Single spec to be replicated
            creation_spec={},
        )

        # Should not raise - single spec can be replicated
        rule.validate(spec, None, [])

    def test_multi_container_matching_specs(self):
        """Test multi-container with matching number of kernel specs."""
        rule = ClusterValidationRule()
        spec = SessionCreationSpec(
            session_creation_id="test-004",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
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

        # Should not raise - specs match cluster size
        rule.validate(spec, None, [])

    def test_multi_container_mismatched_specs(self):
        """Test multi-container with mismatched number of kernel specs."""
        rule = ClusterValidationRule()
        spec = SessionCreationSpec(
            session_creation_id="test-005",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=SessionTypes.INTERACTIVE,
            cluster_mode=None,
            cluster_size=5,  # 5 containers
            priority=10,
            resource_policy={},
            kernel_specs=[
                {"image_ref": MagicMock(canonical="image1")},
                {"image_ref": MagicMock(canonical="image2")},
                {"image_ref": MagicMock(canonical="image3")},
                # Only 3 specs for 5 containers
            ],
            creation_spec={},
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, None, [])
        assert "differs from the cluster size" in str(exc_info.value)
