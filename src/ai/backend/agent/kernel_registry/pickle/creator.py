from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.types import AgentId

from ..loader.pickle import PickleBasedKernelRegistryLoader
from ..writer.pickle import PickleBasedKernelRegistryWriter


@dataclass
class PickleBasedKernelRegistryCreatorArgs:
    scratch_root: Path
    ipc_base_path: Path
    var_base_path: Path
    agent_id: AgentId
    local_instance_id: str


class PickleBasedLoaderWriterCreator:
    """
    Creates a loader and writer for pickle-based kernel registry.
    """

    def __init__(
        self,
        args: PickleBasedKernelRegistryCreatorArgs,
    ) -> None:
        self._registry_file_name = f"last_registry.{args.agent_id}.dat"
        self._legacy_registry_file_path = args.ipc_base_path / self._registry_file_name
        self._fallback_registry_file_path = (
            args.var_base_path / f"last_registry.{args.local_instance_id}.dat"
        )
        self._last_registry_file_path = args.var_base_path / self._registry_file_name

    def create_loader(self) -> PickleBasedKernelRegistryLoader:
        return PickleBasedKernelRegistryLoader(
            self._last_registry_file_path,
            self._fallback_registry_file_path,
            self._legacy_registry_file_path,
        )

    def create_writer(self) -> PickleBasedKernelRegistryWriter:
        return PickleBasedKernelRegistryWriter(self._last_registry_file_path)
