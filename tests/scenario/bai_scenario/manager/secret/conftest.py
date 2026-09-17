"""The secret adapter, assembled for one row.

The key provider pool is read off the row's config, so a row that names the config key
as the write provider gets a pool that encrypts with it.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.secret import SecretFieldType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import FieldGroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.secret.adapter import SecretAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import SecretFieldData
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.secret.provider import SecretOpsProvider
from ai.backend.manager.repositories.secret.repository import SecretRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.secret.processors import SecretProcessors
from ai.backend.manager.services.secret.service import SecretService


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> SecretAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    return SecretAdapter(
        SecretProcessors(
            registry.dangling_field_group(FieldGroupMeta(SecretFieldType()), SecretFieldData),
            SecretService(
                SecretRepository(
                    SecretOpsProvider(engine),
                    KeyProviderPool.from_config(config.config.secret_encryption),
                )
            ),
        )
    )
