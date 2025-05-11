from dataclasses import dataclass

from .backends.kernel import AbstractKernelRegistry
from .backends.types import AbstractBackend


@dataclass
class AgentArgs:
    """
    Arguments for the Agent class.
    """

    backend: AbstractBackend
    kernel_registry: AbstractKernelRegistry


class Agent:
    _backend: AbstractBackend
    _kernel_registry: AbstractKernelRegistry

    def __init__(self, args: AgentArgs):
        """
        Initialize the Agent with the given arguments.
        """
        self._backend = args.backend
        self._kernel_registry = args.kernel_registry
