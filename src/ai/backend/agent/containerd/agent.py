from ai.backend.agent.agent import AbstractAgent

from .kernel import ContainerdKernel, ContainerdKernelCreationContext


class ContainerdAgent(AbstractAgent[ContainerdKernel, ContainerdKernelCreationContext]):
    """Containerd-backed agent (prototype scaffold).

    Concrete operations will be implemented over the CRI gRPC API
    (`grpc.aio` async stubs). All abstract methods inherited from
    `AbstractAgent` are intentionally left unoverridden so the class
    is not yet instantiable; this scaffold exists to validate
    package wiring and discovery only.
    """
