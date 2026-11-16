"""Periodic task that gives the agent's volume status checks their latest volume declarations."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, override

from ai.backend.common.clients.valkey_client.valkey_storage_volume.client import (
    ValkeyStorageVolumeClient,
)
from ai.backend.common.cron import PeriodicTask
from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageVolumeDeclaration
from ai.backend.common.storage.probe.registry import VolumeStatusCheckRegistry
from ai.backend.common.storage.probe.runner import ProbeCheckRunner
from ai.backend.common.storage.volume.mount import VolumeMountStatusCheck
from ai.backend.common.types import AgentId
from ai.backend.logging.structured import StructuredLogger

if TYPE_CHECKING:
    from ai.backend.agent.config.unified import AgentUnifiedConfig

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class _DeclaredCheck:
    declaration: StorageVolumeDeclaration
    check: VolumeMountStatusCheck


@dataclass
class ReadVolumeDeclarationsTaskArgs:
    valkey_storage_volume_client: ValkeyStorageVolumeClient
    agent_ids: Sequence[AgentId]
    registry: VolumeStatusCheckRegistry
    runner: ProbeCheckRunner[StorageVolumeName]
    local_config: AgentUnifiedConfig


class ReadVolumeDeclarationsTask(PeriodicTask):
    """Periodically read the volumes declared for the agents and give the registry and the runner
    one check per volume, keeping the check of an unchanged declaration. An agent whose
    declarations are missing keeps the ones last read for it, as missing tells nothing."""

    _valkey_storage_volume_client: Final[ValkeyStorageVolumeClient]
    _agent_ids: Final[Sequence[AgentId]]
    _registry: Final[VolumeStatusCheckRegistry]
    _runner: Final[ProbeCheckRunner[StorageVolumeName]]
    _local_config: Final[AgentUnifiedConfig]
    _agent_declarations: dict[AgentId, list[StorageVolumeDeclaration]]
    _checks: dict[StorageVolumeName, _DeclaredCheck]

    def __init__(self, args: ReadVolumeDeclarationsTaskArgs) -> None:
        self._valkey_storage_volume_client = args.valkey_storage_volume_client
        self._agent_ids = args.agent_ids
        self._registry = args.registry
        self._runner = args.runner
        self._local_config = args.local_config
        self._agent_declarations = {}
        self._checks = {}

    @property
    @override
    def name(self) -> str:
        return "read_volume_declarations"

    @property
    @override
    def interval(self) -> float:
        return self._local_config.volume_status_check.read_declaration.interval

    @property
    @override
    def initial_delay(self) -> float:
        return self._local_config.volume_status_check.read_declaration.initial_delay

    @override
    async def run(self) -> None:
        declarations = await self._read_declarations()
        self._checks = {
            volume_name: self._declared_check(declaration)
            for volume_name, declaration in declarations.items()
        }
        checks = [declared.check for declared in self._checks.values()]
        self._registry.update(checks)
        self._runner.update(checks)

    async def _read_declarations(self) -> dict[StorageVolumeName, StorageVolumeDeclaration]:
        read = await self._valkey_storage_volume_client.get_volume_declarations(self._agent_ids)
        agent_declarations: dict[AgentId, list[StorageVolumeDeclaration]] = {}
        for agent_id, declarations in read.items():
            if declarations is None:
                log.debug("volume declarations missing", agent_id=agent_id)
                declarations = self._agent_declarations.get(agent_id, [])
            agent_declarations[agent_id] = declarations
        self._agent_declarations = agent_declarations
        return {
            declaration.volume_name: declaration
            for declarations in agent_declarations.values()
            for declaration in declarations
        }

    def _declared_check(self, declaration: StorageVolumeDeclaration) -> _DeclaredCheck:
        current = self._checks.get(declaration.volume_name)
        if current is not None and current.declaration == declaration:
            return current
        check = VolumeMountStatusCheck.create(
            declaration.volume_name,
            declaration.storage_backend_metadata,
            declaration.mount_path,
            self._local_config.volume_status_check,
        )
        return _DeclaredCheck(declaration=declaration, check=check)
