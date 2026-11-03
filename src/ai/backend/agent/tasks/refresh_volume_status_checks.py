"""Periodic task that matches the agent's volume status checks to its volume declarations."""

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
class RefreshVolumeStatusChecksTaskArgs:
    valkey_storage_volume_client: ValkeyStorageVolumeClient
    agent_ids: Sequence[AgentId]
    registry: VolumeStatusCheckRegistry
    runner: ProbeCheckRunner[StorageVolumeName]
    local_config: AgentUnifiedConfig


class RefreshVolumeStatusChecksTask(PeriodicTask):
    """
    Periodically read the volumes declared for the agents and run one check per volume.

    The running checks stay as they are when a read fails. An agent whose declarations are
    missing keeps the declarations last read for it, as missing tells nothing about the volumes.
    """

    _valkey_storage_volume_client: Final[ValkeyStorageVolumeClient]
    _agent_ids: Final[Sequence[AgentId]]
    _registry: Final[VolumeStatusCheckRegistry]
    _runner: Final[ProbeCheckRunner[StorageVolumeName]]
    _local_config: Final[AgentUnifiedConfig]
    _agent_declarations: dict[AgentId, list[StorageVolumeDeclaration]]
    _checks: dict[StorageVolumeName, _DeclaredCheck]

    def __init__(self, args: RefreshVolumeStatusChecksTaskArgs) -> None:
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
        return "refresh_volume_status_checks"

    @property
    @override
    def interval(self) -> float:
        return self._local_config.volume_declaration_refresh.interval

    @property
    @override
    def initial_delay(self) -> float:
        return self._local_config.volume_declaration_refresh.initial_delay

    @override
    async def run(self) -> None:
        declarations = await self._read_declarations()
        for undeclared_volume_name in self._checks.keys() - declarations.keys():
            await self._remove_check(undeclared_volume_name)
        for volume_name, declaration in declarations.items():
            current = self._checks.get(volume_name)
            if current is None:
                self._add_check(declaration)
            elif current.declaration != declaration:
                await self._remove_check(volume_name)
                self._add_check(declaration)

    async def close(self) -> None:
        """Stops every check and shuts down their executors."""
        for volume_name in list(self._checks):
            await self._remove_check(volume_name)

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

    def _add_check(self, declaration: StorageVolumeDeclaration) -> None:
        check = VolumeMountStatusCheck.create(
            declaration.volume_name,
            declaration.storage_backend_metadata,
            declaration.mount_path,
            self._local_config.volume_status_check,
        )
        self._checks[declaration.volume_name] = _DeclaredCheck(declaration=declaration, check=check)
        self._registry.add(check)
        self._runner.add(check)

    async def _remove_check(self, volume_name: StorageVolumeName) -> None:
        declared = self._checks.pop(volume_name)
        await self._runner.remove(volume_name)
        self._registry.remove(volume_name)
        declared.check.close()
