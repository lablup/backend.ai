from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai.backend.agent.kernel import (
    AbstractKernel,
    AgentKernelRegistryKey,
    KernelRegistry,
)
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.types import AgentId, KernelId, SessionId

# Fixtures


@pytest.fixture
def mock_kernel() -> AbstractKernel:
    """Create a mock AbstractKernel instance for testing."""
    kernel = MagicMock(spec=AbstractKernel)
    kernel.kernel_id = KernelId(uuid4())
    kernel.session_id = SessionId(uuid4())
    kernel.agent_id = AgentId("test-agent-1")
    kernel.ownership_data = KernelOwnershipData(
        kernel_id=kernel.kernel_id,
        session_id=kernel.session_id,
        agent_id=kernel.agent_id,
    )
    return kernel


@pytest.fixture
def another_mock_kernel() -> AbstractKernel:
    """Create another mock AbstractKernel instance for testing."""
    kernel = MagicMock(spec=AbstractKernel)
    kernel.kernel_id = KernelId(uuid4())
    kernel.session_id = SessionId(uuid4())
    kernel.agent_id = AgentId("test-agent-2")
    kernel.ownership_data = KernelOwnershipData(
        kernel_id=kernel.kernel_id,
        session_id=kernel.session_id,
        agent_id=kernel.agent_id,
    )
    return kernel


# KernelRegistry tests


def test_kernel_registry_init() -> None:
    """Test KernelRegistry initialization."""
    registry = KernelRegistry()
    assert len(registry) == 0
    assert list(registry) == []


def test_kernel_registry_setitem_and_getitem(mock_kernel: AbstractKernel) -> None:
    """Test adding and retrieving kernels from the registry."""
    registry = KernelRegistry()
    key = AgentKernelRegistryKey(
        agent_id=mock_kernel.agent_id,
        kernel_id=mock_kernel.kernel_id,
    )

    # Add kernel to registry
    registry[key] = mock_kernel

    # Retrieve using composite key
    assert registry[key] == mock_kernel

    # Retrieve using kernel_id only
    assert registry[mock_kernel.kernel_id] == mock_kernel


def test_kernel_registry_delitem(mock_kernel: AbstractKernel) -> None:
    """Test removing kernels from the registry."""
    registry = KernelRegistry()
    key = AgentKernelRegistryKey(
        agent_id=mock_kernel.agent_id,
        kernel_id=mock_kernel.kernel_id,
    )

    registry[key] = mock_kernel
    assert len(registry) == 1

    del registry[key]
    assert len(registry) == 0

    # Verify both internal registries are cleaned up
    with pytest.raises(KeyError):
        _ = registry[key]

    with pytest.raises(KeyError):
        _ = registry[mock_kernel.kernel_id]


def test_kernel_registry_iter(
    mock_kernel: AbstractKernel,
    another_mock_kernel: AbstractKernel,
) -> None:
    """Test iterating over the registry."""
    registry = KernelRegistry()

    key1 = AgentKernelRegistryKey(
        agent_id=mock_kernel.agent_id,
        kernel_id=mock_kernel.kernel_id,
    )
    key2 = AgentKernelRegistryKey(
        agent_id=another_mock_kernel.agent_id,
        kernel_id=another_mock_kernel.kernel_id,
    )

    registry[key1] = mock_kernel
    registry[key2] = another_mock_kernel

    keys = list(registry)
    assert len(keys) == 2
    assert key1 in keys
    assert key2 in keys


def test_kernel_registry_len(
    mock_kernel: AbstractKernel,
    another_mock_kernel: AbstractKernel,
) -> None:
    """Test registry length calculation."""
    registry = KernelRegistry()
    assert len(registry) == 0

    key1 = AgentKernelRegistryKey(
        agent_id=mock_kernel.agent_id,
        kernel_id=mock_kernel.kernel_id,
    )
    registry[key1] = mock_kernel
    assert len(registry) == 1

    key2 = AgentKernelRegistryKey(
        agent_id=another_mock_kernel.agent_id,
        kernel_id=another_mock_kernel.kernel_id,
    )
    registry[key2] = another_mock_kernel
    assert len(registry) == 2


def test_kernel_registry_multiple_agents_same_kernel_id() -> None:
    """Test that the same kernel_id can exist for different agents."""
    registry = KernelRegistry()

    # Create two kernels with the same kernel_id but different agent_ids
    kernel_id = KernelId(uuid4())
    session_id = SessionId(uuid4())
    agent_id_1 = AgentId("agent-1")
    agent_id_2 = AgentId("agent-2")

    kernel1 = MagicMock(spec=AbstractKernel)
    kernel1.kernel_id = kernel_id
    kernel1.session_id = session_id
    kernel1.agent_id = agent_id_1

    kernel2 = MagicMock(spec=AbstractKernel)
    kernel2.kernel_id = kernel_id
    kernel2.session_id = session_id
    kernel2.agent_id = agent_id_2

    key1 = AgentKernelRegistryKey(agent_id=agent_id_1, kernel_id=kernel_id)
    key2 = AgentKernelRegistryKey(agent_id=agent_id_2, kernel_id=kernel_id)

    registry[key1] = kernel1
    registry[key2] = kernel2

    # The second assignment overwrites in the global registry
    # because they share the same kernel_id
    assert len(registry) == 2
    assert registry[key1] == kernel1
    assert registry[key2] == kernel2
    # Global registry will have the last kernel added with this kernel_id
    assert registry[kernel_id] == kernel2


# KernelRegistryAgentView tests


def test_kernel_registry_agent_view_creation(mock_kernel: AbstractKernel) -> None:
    """Test creating an agent-specific view of the registry."""
    registry = KernelRegistry()
    agent_view = registry.agent_mapping(mock_kernel.agent_id)

    assert agent_view._agent_id == mock_kernel.agent_id
    assert agent_view._registry is registry


def test_kernel_registry_agent_view_setitem_and_getitem(
    mock_kernel: AbstractKernel,
) -> None:
    """Test adding and retrieving kernels through agent view."""
    registry = KernelRegistry()
    agent_view = registry.agent_mapping(mock_kernel.agent_id)

    # Add kernel through agent view
    agent_view[mock_kernel.kernel_id] = mock_kernel

    # Retrieve using kernel_id through agent view
    assert agent_view[mock_kernel.kernel_id] == mock_kernel

    # Verify it's also in the main registry
    key = AgentKernelRegistryKey(
        agent_id=mock_kernel.agent_id,
        kernel_id=mock_kernel.kernel_id,
    )
    assert registry[key] == mock_kernel


def test_kernel_registry_agent_view_delitem(mock_kernel: AbstractKernel) -> None:
    """Test removing kernels through agent view."""
    registry = KernelRegistry()
    agent_view = registry.agent_mapping(mock_kernel.agent_id)

    agent_view[mock_kernel.kernel_id] = mock_kernel
    assert len(agent_view) == 1

    del agent_view[mock_kernel.kernel_id]
    assert len(agent_view) == 0

    # Verify it's removed from the main registry too
    key = AgentKernelRegistryKey(
        agent_id=mock_kernel.agent_id,
        kernel_id=mock_kernel.kernel_id,
    )
    with pytest.raises(KeyError):
        _ = registry[key]


def test_kernel_registry_agent_view_iter(mock_kernel: AbstractKernel) -> None:
    """Test iterating over agent view."""
    registry = KernelRegistry()
    agent_view = registry.agent_mapping(mock_kernel.agent_id)

    # Add multiple kernels for the same agent
    kernel_id_1 = KernelId(uuid4())
    kernel_id_2 = KernelId(uuid4())

    kernel1 = MagicMock(spec=AbstractKernel)
    kernel1.kernel_id = kernel_id_1
    kernel1.agent_id = mock_kernel.agent_id

    kernel2 = MagicMock(spec=AbstractKernel)
    kernel2.kernel_id = kernel_id_2
    kernel2.agent_id = mock_kernel.agent_id

    agent_view[kernel_id_1] = kernel1
    agent_view[kernel_id_2] = kernel2

    kernel_ids = list(agent_view)
    assert len(kernel_ids) == 2
    assert kernel_id_1 in kernel_ids
    assert kernel_id_2 in kernel_ids


def test_kernel_registry_agent_view_isolation() -> None:
    """Test that agent views are isolated from each other."""
    registry = KernelRegistry()
    agent_id_1 = AgentId("agent-1")
    agent_id_2 = AgentId("agent-2")

    agent_view_1 = registry.agent_mapping(agent_id_1)
    agent_view_2 = registry.agent_mapping(agent_id_2)

    # Add kernels to different agent views
    kernel_id_1 = KernelId(uuid4())
    kernel_id_2 = KernelId(uuid4())

    kernel1 = MagicMock(spec=AbstractKernel)
    kernel1.kernel_id = kernel_id_1
    kernel1.agent_id = agent_id_1

    kernel2 = MagicMock(spec=AbstractKernel)
    kernel2.kernel_id = kernel_id_2
    kernel2.agent_id = agent_id_2

    agent_view_1[kernel_id_1] = kernel1
    agent_view_2[kernel_id_2] = kernel2

    # Verify isolation
    assert len(agent_view_1) == 1
    assert len(agent_view_2) == 1
    assert kernel_id_1 in list(agent_view_1)
    assert kernel_id_1 not in list(agent_view_2)
    assert kernel_id_2 in list(agent_view_2)
    assert kernel_id_2 not in list(agent_view_1)


def test_kernel_registry_agent_view_len() -> None:
    """Test agent view length calculation."""
    registry = KernelRegistry()
    agent_id = AgentId("test-agent")
    agent_view = registry.agent_mapping(agent_id)

    assert len(agent_view) == 0

    kernel_id = KernelId(uuid4())
    kernel = MagicMock(spec=AbstractKernel)
    kernel.kernel_id = kernel_id
    kernel.agent_id = agent_id

    agent_view[kernel_id] = kernel
    assert len(agent_view) == 1


# KernelRegistryGlobalView tests


def test_kernel_registry_global_view_creation(mock_kernel: AbstractKernel) -> None:
    """Test creating a global view of the registry."""
    registry = KernelRegistry()
    global_view = registry.global_view()

    assert global_view._registry is registry


def test_kernel_registry_global_view_getitem(mock_kernel: AbstractKernel) -> None:
    """Test retrieving kernels through global view."""
    registry = KernelRegistry()
    global_view = registry.global_view()

    # Add kernel to registry
    key = AgentKernelRegistryKey(
        agent_id=mock_kernel.agent_id,
        kernel_id=mock_kernel.kernel_id,
    )
    registry[key] = mock_kernel

    # Retrieve using kernel_id through global view
    assert global_view[mock_kernel.kernel_id] == mock_kernel


def test_kernel_registry_global_view_iter(
    mock_kernel: AbstractKernel,
    another_mock_kernel: AbstractKernel,
) -> None:
    """Test iterating over global view."""
    registry = KernelRegistry()
    global_view = registry.global_view()

    # Add kernels from different agents
    key1 = AgentKernelRegistryKey(
        agent_id=mock_kernel.agent_id,
        kernel_id=mock_kernel.kernel_id,
    )
    key2 = AgentKernelRegistryKey(
        agent_id=another_mock_kernel.agent_id,
        kernel_id=another_mock_kernel.kernel_id,
    )

    registry[key1] = mock_kernel
    registry[key2] = another_mock_kernel

    kernel_ids = list(global_view)
    assert len(kernel_ids) == 2
    assert mock_kernel.kernel_id in kernel_ids
    assert another_mock_kernel.kernel_id in kernel_ids


def test_kernel_registry_global_view_len(
    mock_kernel: AbstractKernel,
    another_mock_kernel: AbstractKernel,
) -> None:
    """Test global view length calculation."""
    registry = KernelRegistry()
    global_view = registry.global_view()

    assert len(global_view) == 0

    key1 = AgentKernelRegistryKey(
        agent_id=mock_kernel.agent_id,
        kernel_id=mock_kernel.kernel_id,
    )
    registry[key1] = mock_kernel
    assert len(global_view) == 1

    key2 = AgentKernelRegistryKey(
        agent_id=another_mock_kernel.agent_id,
        kernel_id=another_mock_kernel.kernel_id,
    )
    registry[key2] = another_mock_kernel
    assert len(global_view) == 2


def test_kernel_registry_global_view_is_readonly() -> None:
    """Test that global view is read-only (Mapping, not MutableMapping)."""
    registry = KernelRegistry()
    global_view = registry.global_view()

    # Global view should not have __setitem__ or __delitem__
    assert (
        not hasattr(global_view, "__setitem__")
        or callable(getattr(global_view, "__setitem__", None)) is False
    )
    assert (
        not hasattr(global_view, "__delitem__")
        or callable(getattr(global_view, "__delitem__", None)) is False
    )


# Integration tests


def test_kernel_registry_views_consistency() -> None:
    """Test that different views of the same registry remain consistent."""
    registry = KernelRegistry()

    agent_id_1 = AgentId("agent-1")
    agent_id_2 = AgentId("agent-2")

    agent_view_1 = registry.agent_mapping(agent_id_1)
    agent_view_2 = registry.agent_mapping(agent_id_2)
    global_view = registry.global_view()

    # Add kernels through different views
    kernel_id_1 = KernelId(uuid4())
    kernel_id_2 = KernelId(uuid4())

    kernel1 = MagicMock(spec=AbstractKernel)
    kernel1.kernel_id = kernel_id_1
    kernel1.agent_id = agent_id_1

    kernel2 = MagicMock(spec=AbstractKernel)
    kernel2.kernel_id = kernel_id_2
    kernel2.agent_id = agent_id_2

    # Add through agent views
    agent_view_1[kernel_id_1] = kernel1
    agent_view_2[kernel_id_2] = kernel2

    # Verify all views see the kernels
    assert len(registry) == 2
    assert len(agent_view_1) == 1
    assert len(agent_view_2) == 1
    assert len(global_view) == 2

    # Verify global view can access both
    assert global_view[kernel_id_1] == kernel1
    assert global_view[kernel_id_2] == kernel2

    # Remove from one agent view
    del agent_view_1[kernel_id_1]

    # Verify consistency across all views
    assert len(registry) == 1
    assert len(agent_view_1) == 0
    assert len(agent_view_2) == 1
    assert len(global_view) == 1

    # Verify the removed kernel is gone from global view
    with pytest.raises(KeyError):
        _ = global_view[kernel_id_1]
