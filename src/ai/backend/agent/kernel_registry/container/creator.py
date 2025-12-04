from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..loader.container import ContainerBasedKernelRegistryLoader
from ..writer.container import ContainerBasedKernelRegistryWriter

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent


@dataclass
class ContainerBasedKernelRegistryCreatorArgs:
    scratch_root: Path
    agent: AbstractAgent


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

    def create_loader(self) -> ContainerBasedKernelRegistryLoader:
        return ContainerBasedKernelRegistryLoader(
            scratch_root=self._scratch_root,
            agent=self._agent,
        )

    def create_writer(self) -> ContainerBasedKernelRegistryWriter:
        return ContainerBasedKernelRegistryWriter(
            scratch_root=self._scratch_root,
        )
