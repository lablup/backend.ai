from dataclasses import dataclass

from ai.backend.agent.backends.docker.image_registry import DockerAgentImageRegistry
from ai.backend.agent.backends.dummy.image_registry import DummyAgentImageRegistry
from ai.backend.agent.backends.image_registry import AbstractAgentImageRegistry
from ai.backend.agent.backends.kubernetes.image_registry import KubernetesAgentImageRegistry
from ai.backend.common.types import CIStrEnum

from .backend import AbstractBackend
from .docker.backend import DockerBackend
from .dummy.backend import DummyBackend
from .kubernetes.backend import KubernetesBackend


@dataclass
class BackendArgs: ...


@dataclass
class ImageRegistryArgs: ...


@dataclass
class KernelFactoryArgs: ...


class AgentBackendType(CIStrEnum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    DUMMY = "dummy"

    def make_backend(self, args: BackendArgs) -> AbstractBackend:
        match self:
            case AgentBackendType.DOCKER:
                return DockerBackend(args)
            case AgentBackendType.KUBERNETES:
                return KubernetesBackend(args)
            case AgentBackendType.DUMMY:
                return DummyBackend(args)
            case _:
                raise ValueError(f"Unsupported backend type: {self}")

    def make_image_registry(self, args: ImageRegistryArgs) -> AbstractAgentImageRegistry:
        match self:
            case AgentBackendType.DOCKER:
                return DockerAgentImageRegistry(args)
            case AgentBackendType.KUBERNETES:
                return KubernetesAgentImageRegistry(args)
            case AgentBackendType.DUMMY:
                return DummyAgentImageRegistry(args)
            case _:
                raise ValueError(f"Unsupported backend type: {self}")
