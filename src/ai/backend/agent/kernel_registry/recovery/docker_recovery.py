from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Self

from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter

from ..pickle.creator import PickleBasedKernelRegistryCreatorArgs, PickleBasedLoaderWriterCreator
from .base_recovery import BaseKernelRegistryRecovery

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class DockerKernelRegistryRecoveryArgs:
    scratch_root: Path
    ipc_base_path: Path
    var_base_path: Path
    agent_id: AgentId
    local_instance_id: str

    # To allow scratch-based loader to list containers
    agent: AbstractAgent


class DockerKernelRegistryRecovery(BaseKernelRegistryRecovery):
    @classmethod
    def create(cls, args: DockerKernelRegistryRecoveryArgs) -> Self:
        pickle_loader_writer_creator = PickleBasedLoaderWriterCreator(
            PickleBasedKernelRegistryCreatorArgs(
                scratch_root=args.scratch_root,
                ipc_base_path=args.ipc_base_path,
                var_base_path=args.var_base_path,
                agent_id=args.agent_id,
                local_instance_id=args.local_instance_id,
            )
        )

        return cls(
            loader=pickle_loader_writer_creator.create_loader(),
            writers=[
                pickle_loader_writer_creator.create_writer(),
            ],
        )
