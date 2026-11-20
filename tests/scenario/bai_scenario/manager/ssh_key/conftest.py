"""The SSH key adapter, assembled for one row."""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.monitors.action_monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.ssh_key.adapter import SSHKeyAdapter
from ai.backend.manager.models.keypair.ssh_key_validator import SSHKeyValidator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ssh_key.repository import SSHKeyRepository
from ai.backend.manager.services.ssh_key.processors import SSHKeyProcessors
from ai.backend.manager.services.ssh_key.service import SSHKeyService


@pytest.fixture
async def adapter(
    engine: ExtendedAsyncSAEngine,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> SSHKeyAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    service = SSHKeyService(SSHKeyRepository(provider), SSHKeyValidator())
    return SSHKeyAdapter(SSHKeyProcessors(registry.group(GroupMeta(UserEntityType())), service))
