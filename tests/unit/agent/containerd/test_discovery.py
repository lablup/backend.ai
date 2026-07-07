from ai.backend.agent.containerd import ContainerdAgentDiscovery, get_agent_discovery
from ai.backend.agent.containerd.agent import (
    ContainerdAgent,
    ContainerdKernelCreationContext,
)
from ai.backend.agent.containerd.kernel import ContainerdCodeRunner, ContainerdKernel
from ai.backend.agent.types import AgentBackend
from ai.backend.agent.types import get_agent_discovery as dispatch_discovery


class TestBackendRegistration:
    def test_enum_has_containerd(self) -> None:
        assert AgentBackend.CONTAINERD.value == "containerd"

    def test_module_discovery_returns_containerd(self) -> None:
        discovery = get_agent_discovery()
        assert isinstance(discovery, ContainerdAgentDiscovery)
        assert discovery.get_agent_cls() is ContainerdAgent

    def test_dispatch_by_enum_imports_containerd_backend(self) -> None:
        discovery = dispatch_discovery(AgentBackend.CONTAINERD)
        assert isinstance(discovery, ContainerdAgentDiscovery)
        assert discovery.get_agent_cls() is ContainerdAgent


class TestConcreteness:
    def test_all_classes_are_concrete(self) -> None:
        for cls in (
            ContainerdAgent,
            ContainerdKernelCreationContext,
            ContainerdKernel,
            ContainerdCodeRunner,
        ):
            assert getattr(cls, "__abstractmethods__", frozenset()) == frozenset(), (
                f"{cls.__name__} still has unimplemented abstract methods"
            )
