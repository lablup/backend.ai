"""The login client type adapter, assembled for one row. Every call runs against ops."""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.login_client_type import LoginClientTypeEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.login_client_type.processors import LoginClientTypeProcessors


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> LoginClientTypeAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    return LoginClientTypeAdapter(
        LoginClientTypeProcessors(registry.group(GroupMeta(LoginClientTypeEntityType())))
    )
