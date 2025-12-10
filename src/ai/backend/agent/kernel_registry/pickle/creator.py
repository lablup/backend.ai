from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Self

from ai.backend.common.types import AgentId

from ..loader.pickle import PickleBasedKernelRegistryLoader
from ..writer.pickle import PickleBasedKernelRegistryWriter

if TYPE_CHECKING:
    from ai.backend.agent.agent import AgentClass


@dataclass
class PickleBasedKernelRegistryCreatorArgs:
    scratch_root: Path
    ipc_base_path: Path
    var_base_path: Path

    agent_class: AgentClass
    agent_id: AgentId
    local_instance_id: str


class PickleBasedLoaderWriterCreator:
    """
    Creates a loader and writer for pickle-based kernel registry.
    """

    def __init__(
        self,
        registry_file_path: Path,
        legacy_registry_file_path: Path,
    ) -> None:
        self._registry_file = registry_file_path
        self._legacy_registry_file = legacy_registry_file_path

    @classmethod
    def _last_registry_file_name(
        cls,
        args: PickleBasedKernelRegistryCreatorArgs,
    ) -> str:
        from ai.backend.agent.agent import AgentClass

        match args.agent_class:
            case AgentClass.PRIMARY:
                return cls._primary_last_registry_file(args.local_instance_id)
            case AgentClass.AUXILIARY:
                return cls._auxiliary_last_registry_file(args.agent_id)

    @classmethod
    def _primary_last_registry_file(cls, local_instance_id: str) -> str:
        return f"last_registry.{local_instance_id}.dat"

    @classmethod
    def _auxiliary_last_registry_file(cls, agent_id: AgentId) -> str:
        return f"last_registry.{agent_id}.dat"

    @classmethod
    def _resolve_conflicting_registry_file(
        cls,
        base_dir: Path,
        agent_id: AgentId,
        local_instance_id: str,
    ) -> Path:
        primary_agent_file = base_dir / cls._primary_last_registry_file(local_instance_id)
        auxiliary_agent_file = base_dir / cls._auxiliary_last_registry_file(agent_id)

        match primary_agent_file.is_file(), auxiliary_agent_file.is_file():
            case True, True if (
                primary_agent_file.stat().st_mtime < auxiliary_agent_file.stat().st_mtime
            ):
                # Case 1: If both files exist for primary agent, and ID-based file is more recent.
                return auxiliary_agent_file
            case False, True:
                # Case 2: Only ID-based file exists.
                return auxiliary_agent_file
            case _:
                return primary_agent_file

    @classmethod
    def create(cls, args: PickleBasedKernelRegistryCreatorArgs) -> Self:
        from ai.backend.agent.agent import AgentClass

        if args.agent_class != AgentClass.PRIMARY:
            ipc_last_registry_file = args.ipc_base_path / cls._last_registry_file_name(args)
            last_registry_file = args.var_base_path / cls._last_registry_file_name(args)
        else:
            ipc_last_registry_file = cls._resolve_conflicting_registry_file(
                args.ipc_base_path, args.agent_id, args.local_instance_id
            )
            last_registry_file = cls._resolve_conflicting_registry_file(
                args.var_base_path, args.agent_id, args.local_instance_id
            )
        return cls(
            registry_file_path=last_registry_file,
            legacy_registry_file_path=ipc_last_registry_file,
        )

    def create_loader(self) -> PickleBasedKernelRegistryLoader:
        return PickleBasedKernelRegistryLoader(
            self._registry_file,
            self._legacy_registry_file,
        )

    def create_writer(self) -> PickleBasedKernelRegistryWriter:
        return PickleBasedKernelRegistryWriter(self._registry_file)
