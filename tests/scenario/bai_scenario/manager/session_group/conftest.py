"""The session group adapter, assembled for one row.

What it is built with comes from the root conftest.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.session_group.processors import SessionGroupProcessors
from ai.backend.manager.services.session_group.service import SessionGroupService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> SessionGroupAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    return SessionGroupAdapter(
        SessionGroupProcessors(
            registry.group(GroupMeta(SessionGroupEntityType())),
            SessionGroupService(OpsRepository(provider)),
        ),
    )
