"""The system session environ adapter, assembled for one row.

Only the value source list and the create keep a service; the other calls run
against ops. The value resolvers are not reached by these tables, so the registry is
empty.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.system_session_environ.adapter import (
    SystemSessionEnvironAdapter,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.system_session_environ.repository import (
    SystemSessionEnvironRepository,
)
from ai.backend.manager.repositories.system_session_environ.value_resolver import (
    SystemSessionEnvironValueResolverRegistry,
)
from ai.backend.manager.services.system_session_environ.processors import (
    SystemSessionEnvironProcessors,
)
from ai.backend.manager.services.system_session_environ.service import (
    SystemSessionEnvironService,
)


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> SystemSessionEnvironAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    service = SystemSessionEnvironService(
        SystemSessionEnvironRepository(provider, SystemSessionEnvironValueResolverRegistry([]))
    )
    return SystemSessionEnvironAdapter(
        SystemSessionEnvironProcessors(
            registry.group(GroupMeta(SystemSessionEnvironEntityType())), service
        )
    )
