"""Tests for validation rules."""

import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import MagicMock

import pytest
import yarl

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelEnqueueingConfig,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.kernel import QuotaExceeded
from ai.backend.manager.models import NetworkRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    ContainerUserInfo,
    ImageInfo,
    ScalingGroupNetworkInfo,
    SessionCreationContext,
    SessionCreationSpec,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.cluster import (
    ClusterValidationRule,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.rules import (
    ContainerLimitRule,
    ServicePortRule,
)
from ai.backend.manager.types import UserScope


@pytest.fixture
def basic_context() -> SessionCreationContext:
    """Create a basic SessionCreationContext."""
    return SessionCreationContext(
        scaling_group_network=ScalingGroupNetworkInfo(use_host_network=False),
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


@pytest.fixture
def session_spec_factory() -> Callable[..., SessionCreationSpec]:
    def create_spec(
        session_creation_id: str = "test-001",
        session_name: str = "test-session",
        access_key: AccessKey = AccessKey("test-key"),
        user_scope: UserScope = UserScope(
            domain_name="default",
            group_id=uuid.uuid4(),
            user_uuid=uuid.uuid4(),
            user_role="user",
        ),
        session_type: SessionTypes = SessionTypes.INTERACTIVE,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        cluster_size: int = 1,
        priority: int = 10,
        resource_policy: dict | None = None,
        kernel_specs: list[KernelEnqueueingConfig] | None = None,
        creation_spec: dict | None = None,
        scaling_group: Optional[str] = None,
        session_tag: Optional[str] = None,
        starts_at: Optional[datetime] = None,
        batch_timeout: Optional[timedelta] = None,
        dependency_sessions: Optional[list[SessionId]] = None,
        callback_url: Optional[yarl.URL] = None,
        route_id: Optional[uuid.UUID] = None,
        sudo_session_enabled: bool = False,
        network: Optional[NetworkRow] = None,
        designated_agent_list: Optional[list[str]] = None,
        internal_data: Optional[dict] = None,
        public_sgroup_only: bool = True,
    ) -> SessionCreationSpec:
        return SessionCreationSpec(
            session_creation_id=session_creation_id,
            session_name=session_name,
            access_key=access_key,
            user_scope=user_scope,
            session_type=session_type,
            cluster_mode=cluster_mode,
            cluster_size=cluster_size,
            priority=priority,
            resource_policy=resource_policy or {},
            kernel_specs=kernel_specs or [],
            creation_spec=creation_spec or {},
            scaling_group=scaling_group,
            session_tag=session_tag,
            starts_at=starts_at,
            batch_timeout=batch_timeout,
            dependency_sessions=dependency_sessions,
            callback_url=callback_url,
            route_id=route_id,
            sudo_session_enabled=sudo_session_enabled,
            network=network,
            designated_agent_list=designated_agent_list,
            internal_data=internal_data,
            public_sgroup_only=public_sgroup_only,
        )

    return create_spec


class TestContainerLimitRule:
    """Test cases for ContainerLimitRule."""

    def test_within_limit(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test cluster size within limits."""
        rule = ContainerLimitRule()
        spec = session_spec_factory(
            session_creation_id="test-001",
            cluster_size=3,
            resource_policy={"max_containers_per_session": 5},
        )

        # Should not raise
        rule.validate(spec, basic_context)

    def test_exceeds_limit(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test cluster size exceeding limits."""
        rule = ContainerLimitRule()
        spec = session_spec_factory(
            session_creation_id="test-002",
            cluster_size=10,
            resource_policy={"max_containers_per_session": 5},
        )

        with pytest.raises(QuotaExceeded) as exc_info:
            rule.validate(spec, basic_context)
        assert "cannot create session with more than 5 containers" in str(exc_info.value)

    def test_default_limit(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test default limit when not specified."""
        rule = ContainerLimitRule()
        spec = session_spec_factory(
            session_creation_id="test-003",
            cluster_size=2,
            resource_policy={},  # No limit specified, defaults to 1
        )

        with pytest.raises(QuotaExceeded):
            rule.validate(spec, basic_context)


class TestServicePortRule:
    """Test cases for ServicePortRule."""

    def test_reserved_ports(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test validation of reserved ports."""
        rule = ServicePortRule()
        spec = session_spec_factory(
            session_creation_id="test-001",
            kernel_specs=[
                {
                    "image_ref": type("ImageRef", (), {"canonical": "test-image"})(),
                    "creation_config": {
                        "preopen_ports": [2000, 8080],  # 2000 is reserved
                    },
                }
            ],
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context)
        assert "reserved for internal use" in str(exc_info.value)

    def test_service_port_overlap(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test validation of overlapping service ports."""
        rule = ServicePortRule()
        spec = session_spec_factory(
            session_creation_id="test-002",
            kernel_specs=[
                {
                    "image_ref": type("ImageRef", (), {"canonical": "test-image"})(),
                    "creation_config": {
                        "preopen_ports": [8888, 9000],  # 8888 overlaps with jupyter service port
                    },
                }
            ],
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context)
        assert "overlap with service port" in str(exc_info.value)

    def test_creation_config_preopen_ports(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test validation of preopen_ports from creation_config."""
        rule = ServicePortRule()
        spec = session_spec_factory(
            session_creation_id="test-003",
            kernel_specs=[{"image_ref": type("ImageRef", (), {"canonical": "test-image"})()}],
            creation_spec={
                "preopen_ports": [2001, 3000],  # 2001 is reserved
            },
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context)
        assert "reserved for internal use" in str(exc_info.value)

    def test_valid_ports(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test validation with valid ports."""
        rule = ServicePortRule()
        spec = session_spec_factory(
            session_creation_id="test-004",
            kernel_specs=[
                {
                    "image_ref": type("ImageRef", (), {"canonical": "test-image"})(),
                    "creation_config": {
                        "preopen_ports": [3000, 4000, 5000],  # All valid ports
                    },
                }
            ],
        )

        # Should not raise
        rule.validate(spec, basic_context)

    def test_all_reserved_ports(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test all reserved ports (2000, 2001, 2200, 7681)."""
        rule = ServicePortRule()
        reserved_ports = [2000, 2001, 2200, 7681]

        for port in reserved_ports:
            spec = session_spec_factory(
                session_creation_id=f"test-reserved-{port}",
                creation_spec={
                    "preopen_ports": [port],
                },
            )

            with pytest.raises(InvalidAPIParameters) as exc_info:
                rule.validate(spec, basic_context)
            assert "reserved for internal use" in str(exc_info.value)


class TestClusterValidationRule:
    """Test cases for ClusterValidationRule."""

    def test_no_kernel_specs(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test validation with no kernel specs."""
        rule = ClusterValidationRule()
        spec = session_spec_factory(
            session_creation_id="test-001",
            kernel_specs=[],  # Empty kernel specs
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context)
        assert "at least one kernel specification" in str(exc_info.value).lower()

    def test_single_container(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test validation for single container session."""
        rule = ClusterValidationRule()
        spec = session_spec_factory(
            session_creation_id="test-002",
            kernel_specs=[{"image_ref": MagicMock(canonical="test-image")}],
        )

        # Should not raise for single container
        rule.validate(spec, basic_context)

    def test_multi_container_single_spec(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test multi-container with single kernel spec (valid for replication)."""
        rule = ClusterValidationRule()
        spec = session_spec_factory(
            session_creation_id="test-003",
            cluster_size=4,
            kernel_specs=[
                {"image_ref": MagicMock(canonical="test-image")}
            ],  # Single spec to be replicated
        )

        # Should not raise - single spec can be replicated
        rule.validate(spec, basic_context)

    def test_multi_container_matching_specs(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test multi-container with matching number of kernel specs."""
        rule = ClusterValidationRule()
        spec = session_spec_factory(
            session_creation_id="test-004",
            cluster_size=3,
            kernel_specs=[
                {"image_ref": MagicMock(canonical="image1")},
                {"image_ref": MagicMock(canonical="image2")},
                {"image_ref": MagicMock(canonical="image3")},
            ],
        )

        # Should not raise - specs match cluster size
        rule.validate(spec, basic_context)

    def test_multi_container_mismatched_specs(
        self,
        basic_context: SessionCreationContext,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test multi-container with mismatched number of kernel specs."""
        rule = ClusterValidationRule()
        spec = session_spec_factory(
            session_creation_id="test-005",
            cluster_size=5,  # 5 containers
            kernel_specs=[
                {"image_ref": MagicMock(canonical="image1")},
                {"image_ref": MagicMock(canonical="image2")},
                {"image_ref": MagicMock(canonical="image3")},
                # Only 3 specs for 5 containers
            ],
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            rule.validate(spec, basic_context)
        assert "differs from the cluster size" in str(exc_info.value)
