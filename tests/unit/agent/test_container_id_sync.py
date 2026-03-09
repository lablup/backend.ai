"""
Tests for BA-4891: AbstractKernel.set_container_id() method.

Verifies that set_container_id() synchronizes both the instance attribute
and the UserDict data dict in a single call.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from ai.backend.agent.docker.kernel import DockerKernel
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, ContainerId, KernelId, SessionId


@pytest.fixture
def mock_kernel_obj() -> DockerKernel:
    """Create a mock kernel object for testing."""
    kernel_id = KernelId("test-kernel-id")
    session_id = SessionId("test-session-id")
    agent_id = AgentId("test-agent-id")

    ownership_data = KernelOwnershipData(
        kernel_id=kernel_id,
        session_id=session_id,
        agent_id=agent_id,
    )
    image = ImageRef(
        name="test-image",
        project="test-project",
        registry="registry.local",
        tag="latest",
        architecture="x86_64",
        is_local=False,
    )
    return DockerKernel(
        ownership_data=ownership_data,
        network_id="test-network",
        image=image,
        version=1,
        network_driver="bridge",
        agent_config={},
        resource_spec=Mock(),
        service_ports=[],
        environ={},
        data={},
    )


class TestSetContainerId:
    """Tests for AbstractKernel.set_container_id()."""

    def test_sets_both_instance_attr_and_data_dict(
        self, mock_kernel_obj: DockerKernel
    ) -> None:
        """set_container_id() should update both the instance attribute and data dict."""
        assert mock_kernel_obj.container_id is None
        assert "container_id" not in mock_kernel_obj.data

        cid = ContainerId("test-container-abc123")
        mock_kernel_obj.set_container_id(cid)

        assert mock_kernel_obj.container_id == cid
        assert mock_kernel_obj["container_id"] == cid
        assert mock_kernel_obj.data["container_id"] == cid

    def test_second_call_updates_both_sources(
        self, mock_kernel_obj: DockerKernel
    ) -> None:
        """A second set_container_id() call should update both sources to the new value."""
        first = ContainerId("first-container-111")
        second = ContainerId("second-container-222")

        mock_kernel_obj.set_container_id(first)
        assert mock_kernel_obj.container_id == first
        assert mock_kernel_obj["container_id"] == first

        mock_kernel_obj.set_container_id(second)
        assert mock_kernel_obj.container_id == second
        assert mock_kernel_obj["container_id"] == second
