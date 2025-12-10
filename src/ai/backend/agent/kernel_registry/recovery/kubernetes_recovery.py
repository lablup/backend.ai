from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Self

from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter

from ..loader.pickle import PickleBasedKernelRegistryLoader
from ..writer.pickle import PickleBasedKernelRegistryWriter
from .base_recovery import BaseKernelRegistryRecovery

if TYPE_CHECKING:
    pass

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class KubernetesKernelRegistryRecoveryArgs:
    scratch_root: Path
    ipc_base_path: Path
    var_base_path: Path
    agent_id: AgentId
    local_instance_id: str


class KubernetesKernelRegistryRecovery(BaseKernelRegistryRecovery):
    @classmethod
    def create(cls, args: KubernetesKernelRegistryRecoveryArgs) -> Self:
        registry_file_name = f"last_registry.{args.agent_id}.dat"
        legacy_registry_file_path = args.ipc_base_path / registry_file_name
        last_registry_file_path = args.var_base_path / registry_file_name

        return cls(
            loader=PickleBasedKernelRegistryLoader(
                last_registry_file_path,
                legacy_registry_file_path,
            ),
            writers=[PickleBasedKernelRegistryWriter(last_registry_file_path)],
        )
