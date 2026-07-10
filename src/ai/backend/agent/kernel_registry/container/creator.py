from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ai.backend.agent.kernel_registry.loader.container import ContainerBasedKernelRegistryLoader
from ai.backend.agent.kernel_registry.types import KernelRecoveryData
from ai.backend.agent.kernel_registry.writer.container import ContainerBasedKernelRegistryWriter

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent
    from ai.backend.agent.kernel import AbstractKernel


@dataclass
class ContainerBasedKernelRegistryCreatorArgs:
    scratch_root: Path
    agent: AbstractAgent[Any, Any]
    # Optional: reconstruct a backend-specific kernel from the recovery data (defaults to the
    # docker kernel inside the loader when None). The containerd agent passes to_containerd_kernel.
    kernel_factory: Callable[[KernelRecoveryData], AbstractKernel] | None = None


class ContainerBasedLoaderWriterCreator:
    """
    Creates a loader and writer for container-based kernel registry.
    """

    def __init__(
        self,
        args: ContainerBasedKernelRegistryCreatorArgs,
    ) -> None:
        self._scratch_root = args.scratch_root
        self._agent = args.agent
        self._kernel_factory = args.kernel_factory

    def create_loader(self) -> ContainerBasedKernelRegistryLoader:
        return ContainerBasedKernelRegistryLoader(
            scratch_root=self._scratch_root,
            agent=self._agent,
            kernel_factory=self._kernel_factory,
        )

    def create_writer(self) -> ContainerBasedKernelRegistryWriter:
        return ContainerBasedKernelRegistryWriter(
            scratch_root=self._scratch_root,
        )
