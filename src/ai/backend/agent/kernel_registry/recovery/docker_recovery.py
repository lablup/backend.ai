from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter

from .base_recovery import BaseKernelRegistryRecovery

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent, AgentClass

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class DockerKernelRegistryRecoveryArgs:
    scratch_root: Path
    ipc_base_path: Path
    var_base_path: Path
    agent_class: AgentClass
    agent_id: AgentId
    local_instance_id: str

    # To allow scratch-based loader to list containers
    agent: AbstractAgent


class DockerKernelRegistryRecovery(BaseKernelRegistryRecovery):
    pass
