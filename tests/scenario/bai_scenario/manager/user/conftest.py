"""The user adapter, assembled for one row.

Creating a user is the operation these rows exercise. It reaches the user service and
the domain lookup; what only session or folder work reaches is left unwired.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_scenario.runner.unwired import unwired
from bai_scenario.valkey import ScenarioValkey

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    valkey: ScenarioValkey,
) -> UserAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    key_pool = KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN)
    user = UserProcessors(
        registry.group(GroupMeta(UserEntityType())),
        UserService(
            unwired(StorageSessionManager, "only folder work reaches it"),
            valkey.stat,
            unwired(AgentRegistry, "only session work reaches the agents"),
            UserRepository(engine, provider, ShareOpsProvider(engine), key_pool),
            unwired(SchedulingController, "only enqueue schedules"),
        ),
    )
    domain = DomainProcessors(
        registry.group(GroupMeta(DomainEntityType())),
        DomainService(DomainRepository(engine, provider)),
        [],
    )
    return UserAdapter(user, domain, config.config.auth, key_pool)
