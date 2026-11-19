"""The SSH keypair adapter, assembled for one row."""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.ssh_keypair.adapter import SSHKeypairAdapter
from ai.backend.manager.models.keypair.ssh_key_validator import SSHKeyValidator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ssh_keypair.repository import SSHKeypairRepository
from ai.backend.manager.services.ssh_keypair.processors import SSHKeypairProcessors
from ai.backend.manager.services.ssh_keypair.service import SSHKeypairService


@pytest.fixture
async def adapter(
    engine: ExtendedAsyncSAEngine,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> SSHKeypairAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    service = SSHKeypairService(SSHKeypairRepository(provider), SSHKeyValidator())
    return SSHKeypairAdapter(
        SSHKeypairProcessors(registry.group(GroupMeta(UserEntityType())), service)
    )
