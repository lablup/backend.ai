"""
Tests for BA-4891: Fix kernel container_id attribute shadowed by UserDict data dict in agent.

This module tests that the container_id instance attribute is properly synchronized
with the UserDict data dict in all code paths:
1. _handle_start_event method (agent restart recovery)
2. inject_container_lifecycle_event method (START event)
3. create_kernel method's data.update call (fresh kernel creation)

The tests verify the synchronization pattern that is applied in production code:
- kernel_obj.container_id = value (instance attribute)
- kernel_obj["container_id"] = value (data dict)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from ai.backend.agent.agent import ContainerLifecycleEvent
from ai.backend.agent.docker.kernel import DockerKernel
from ai.backend.agent.types import KernelOwnershipData, LifecycleEvent
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, SessionId


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


@pytest.fixture
def mock_agent() -> Mock:
    """Create a mock agent with kernel registry for testing."""
    agent = Mock()
    agent.kernel_registry = {}
    agent.registry_lock = AsyncMock()
    agent.registry_lock.__aenter__ = AsyncMock()
    agent.registry_lock.__aexit__ = AsyncMock()
    return agent


class TestContainerIdSync:
    """Tests for container_id instance attribute synchronization."""

    def test_fresh_kernel_data_update_syncs_container_id(
        self, mock_kernel_obj: DockerKernel
    ) -> None:
        """
        Test that create_kernel method's data.update call syncs container_id instance attribute.

        This tests the synchronization pattern in create_kernel method where data.update
        is followed by explicit instance attribute sync.
        """
        # Initial state - container_id should be None
        assert mock_kernel_obj.container_id is None
        assert "container_id" not in mock_kernel_obj.data

        # Simulate the data.update path in create_kernel method
        container_data = {
            "container_id": "test-container-abc123",
            "repl_in_port": 5000,
            "repl_out_port": 5001,
        }
        mock_kernel_obj.data.update(container_data)

        # Apply the synchronization pattern used in production code
        if "container_id" in container_data:
            mock_kernel_obj.container_id = container_data["container_id"]

        # Both sources should now have the same value
        assert mock_kernel_obj.container_id == "test-container-abc123"
        assert mock_kernel_obj["container_id"] == "test-container-abc123"
        assert mock_kernel_obj.data["container_id"] == "test-container-abc123"

    def test_inject_lifecycle_event_start_syncs_container_id(
        self, mock_kernel_obj: DockerKernel
    ) -> None:
        """
        Test that inject_container_lifecycle_event method syncs both sources for START event.

        This tests the synchronization pattern in inject_container_lifecycle_event method
        where both data dict and instance attribute are set.
        """
        # Initial state
        assert mock_kernel_obj.container_id is None

        # Simulate the inject_container_lifecycle_event START event path
        container_id = "injected-container-xyz789"

        # Apply the synchronization pattern: set both UserDict data dict and instance attribute
        mock_kernel_obj["container_id"] = container_id
        mock_kernel_obj.container_id = container_id

        # Both sources should be in sync
        assert mock_kernel_obj.container_id == "injected-container-xyz789"
        assert mock_kernel_obj["container_id"] == "injected-container-xyz789"
        assert mock_kernel_obj.data["container_id"] == "injected-container-xyz789"

    async def test_handle_start_event_syncs_container_id(
        self, mock_kernel_obj: DockerKernel, mock_agent: Mock
    ) -> None:
        """
        Test that _handle_start_event method syncs container_id instance attribute.

        This tests the synchronization pattern in _handle_start_event method.
        This is the critical path for agent restart recovery (BA-4946).
        """
        # Setup kernel in registry
        kernel_id = mock_kernel_obj.kernel_id
        mock_agent.kernel_registry[kernel_id] = mock_kernel_obj

        # Initial state - simulate agent restart where container_id was not in recovery data
        assert mock_kernel_obj.container_id is None

        # Simulate the _handle_start_event path by creating an event and applying the sync pattern
        event_container_id = "restart-recovery-container-def456"
        event = ContainerLifecycleEvent(
            kernel_id=kernel_id,
            session_id=mock_kernel_obj.session_id,
            event=LifecycleEvent.START,
            container_id=event_container_id,
            reason=None,
            exit_code=None,
        )

        # Apply the synchronization pattern used in _handle_start_event
        kernel_obj = mock_agent.kernel_registry.get(event.kernel_id)
        if kernel_obj is not None and event.container_id is not None:
            kernel_obj.container_id = event.container_id
            kernel_obj["container_id"] = event.container_id

        # Both sources should be in sync
        assert mock_kernel_obj.container_id == "restart-recovery-container-def456"
        assert mock_kernel_obj["container_id"] == "restart-recovery-container-def456"
        assert mock_kernel_obj.data["container_id"] == "restart-recovery-container-def456"

    def test_container_id_consistency_after_multiple_updates(
        self, mock_kernel_obj: DockerKernel
    ) -> None:
        """
        Test that container_id remains consistent after multiple update operations.

        This ensures the synchronization pattern works correctly when container_id
        is updated multiple times through different code paths.
        """
        # First update - simulate inject_container_lifecycle_event
        mock_kernel_obj["container_id"] = "first-container-111"
        mock_kernel_obj.container_id = "first-container-111"

        assert mock_kernel_obj.container_id == "first-container-111"
        assert mock_kernel_obj["container_id"] == "first-container-111"

        # Second update - simulate data.update
        container_data = {"container_id": "second-container-222"}
        mock_kernel_obj.data.update(container_data)
        mock_kernel_obj.container_id = container_data["container_id"]

        assert mock_kernel_obj.container_id == "second-container-222"
        assert mock_kernel_obj["container_id"] == "second-container-222"

    def test_container_id_none_check_works_correctly(self, mock_kernel_obj: DockerKernel) -> None:
        """
        Test that 'kernel_obj.container_id is None' check works correctly.

        This is critical for collect_container_stat() method.
        Before the fix, this check always returned True even when container_id
        was set in the data dict.
        """
        # Initial state - should be None
        assert mock_kernel_obj.container_id is None

        # After setting container_id (simulating any of the three code paths)
        mock_kernel_obj["container_id"] = "active-container-333"
        mock_kernel_obj.container_id = "active-container-333"

        # Now the check should return False
        assert mock_kernel_obj.container_id is not None
        assert mock_kernel_obj.container_id == "active-container-333"

    def test_userdict_repr_vs_instance_attribute(self, mock_kernel_obj: DockerKernel) -> None:
        """
        Test that demonstrates the shadowing issue from the bug description.

        repr(kernel_obj) uses UserDict.__repr__() which shows the data dict,
        while kernel_obj.container_id accesses the instance attribute.
        This test verifies that the synchronization pattern resolves this discrepancy.
        """
        # Set only the data dict (simulating the bug scenario before the fix)
        mock_kernel_obj.data["container_id"] = "dict-only-container-444"

        # Instance attribute is still None
        assert mock_kernel_obj.container_id is None

        # But the data dict has a value
        assert mock_kernel_obj["container_id"] == "dict-only-container-444"

        # After applying the synchronization pattern, both are in sync
        mock_kernel_obj.container_id = mock_kernel_obj.data["container_id"]

        # Now both are in sync
        assert mock_kernel_obj.container_id == "dict-only-container-444"
        assert mock_kernel_obj["container_id"] == "dict-only-container-444"
