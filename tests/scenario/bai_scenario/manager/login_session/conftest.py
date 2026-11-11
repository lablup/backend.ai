"""The login session adapter, assembled for one row.

What only the login flow itself reaches is left unwired.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.login_session.adapter import LoginSessionAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.client_ip_masking.repository import (
    ClientIPMaskingRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.auth.service import AuthService
from bai_scenario.runner.unwired import unwired
from bai_scenario.valkey import ScenarioValkey


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    valkey: ScenarioValkey,
) -> LoginSessionAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    key_pool = KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN)
    auth = AuthProcessors(
        registry.group(GroupMeta(GlobalEntityType())),
        registry.group(GroupMeta(UserEntityType())),
        AuthService(
            unwired(HookPluginContext, "only the login flow runs hooks"),
            AuthRepository(engine, V2DBOpsProvider(engine), key_pool),
            unwired(ManagerConfigProvider, "only the login flow reads the config"),
            valkey.session,
            unwired(UserResourcePolicyRepository, "only signing up reads user policies"),
            unwired(UserRepository, "only the login flow reads users"),
            unwired(ProjectRepository, "only role lookups read projects"),
            ClientIPMaskingRepository(engine),
            key_pool,
        ),
    )
    return LoginSessionAdapter(auth)
