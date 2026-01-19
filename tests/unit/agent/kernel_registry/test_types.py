from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.kernel_registry.types import KernelRecoveryData
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, ResourceSlot, SessionId, SessionTypes


@pytest.fixture
def mock_kernel_data() -> dict[str, Any]:
    """Default kernel data with all required fields."""
    return {
        "block_service_ports": False,
        "domain_socket_proxies": [],
        "repl_in_port": 2000,
        "repl_out_port": 2001,
    }


@pytest.fixture
def mock_resource_spec() -> KernelResourceSpec:
    """Real KernelResourceSpec instance for testing."""
    return KernelResourceSpec(
        slots=ResourceSlot(),
        allocations={},
        scratch_disk_size=0,
    )


@pytest.fixture
def mock_docker_kernel(
    mock_kernel_data: dict[str, Any],
    mock_resource_spec: KernelResourceSpec,
) -> MagicMock:
    """Mock DockerKernel with required attributes."""
    kernel_id = KernelId(uuid.uuid4())
    session_id = SessionId(uuid.uuid4())
    agent_id = AgentId("test-agent")

    kernel = MagicMock()
    kernel.kernel_id = kernel_id
    kernel.agent_id = agent_id
    kernel.image = ImageRef(
        name="python",
        project="stable",
        tag="3.10-ubuntu22.04",
        registry="cr.backend.ai",
        architecture="x86_64",
        is_local=False,
    )
    kernel.session_type = SessionTypes.INTERACTIVE
    kernel.ownership_data = KernelOwnershipData(
        kernel_id=kernel_id,
        session_id=session_id,
        agent_id=agent_id,
    )
    kernel.network_id = str(uuid.uuid4())
    kernel.version = 1
    kernel.network_driver = "bridge"
    kernel.resource_spec = mock_resource_spec
    kernel.service_ports = []
    kernel.environ = {}
    kernel.data = mock_kernel_data
    return kernel


class TestKernelRecoveryDataFromDockerKernel:
    """Tests for KernelRecoveryData.from_docker_kernel() method."""

    def test_from_docker_kernel_with_all_fields(self, mock_docker_kernel: Any) -> None:
        """Parse successfully when all fields are present."""
        result = KernelRecoveryData.from_docker_kernel(mock_docker_kernel)

        assert result.block_service_ports is False
        assert result.domain_socket_proxies == []
        assert result.repl_in_port == 2000
        assert result.repl_out_port == 2001

    def test_from_docker_kernel_without_block_service_ports(self, mock_docker_kernel: Any) -> None:
        """Use default False when block_service_ports key is missing."""
        mock_docker_kernel.data = {
            "domain_socket_proxies": [],
            "repl_in_port": 2000,
            "repl_out_port": 2001,
        }

        result = KernelRecoveryData.from_docker_kernel(mock_docker_kernel)

        assert result.block_service_ports is False

    def test_from_docker_kernel_without_domain_socket_proxies(
        self, mock_docker_kernel: Any
    ) -> None:
        """Use default [] when domain_socket_proxies key is missing."""
        mock_docker_kernel.data = {
            "block_service_ports": True,
            "repl_in_port": 2000,
            "repl_out_port": 2001,
        }

        result = KernelRecoveryData.from_docker_kernel(mock_docker_kernel)

        assert result.domain_socket_proxies == []

    def test_from_docker_kernel_missing_repl_in_port_raises_keyerror(
        self, mock_docker_kernel: Any
    ) -> None:
        """Raise KeyError when repl_in_port is missing."""
        mock_docker_kernel.data = {
            "block_service_ports": False,
            "domain_socket_proxies": [],
            "repl_out_port": 2001,
        }

        with pytest.raises(KeyError, match="repl_in_port"):
            KernelRecoveryData.from_docker_kernel(mock_docker_kernel)

    def test_from_docker_kernel_missing_repl_out_port_raises_keyerror(
        self, mock_docker_kernel: Any
    ) -> None:
        """Raise KeyError when repl_out_port is missing."""
        mock_docker_kernel.data = {
            "block_service_ports": False,
            "domain_socket_proxies": [],
            "repl_in_port": 2000,
        }

        with pytest.raises(KeyError, match="repl_out_port"):
            KernelRecoveryData.from_docker_kernel(mock_docker_kernel)
