"""The user adapter and the two adapters over the fields a user owns, assembled for one row.

What only session or folder work reaches is left unwired, and so is what only the login
flow itself reaches.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.login_history.adapter import LoginHistoryAdapter
from ai.backend.manager.api.adapters.login_session.adapter import LoginSessionAdapter
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.keypair.ssh_key_validator import SSHKeyValidator
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.client_ip_masking.repository import (
    ClientIPMaskingRepository,
)
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.domain.provider import DomainOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.auth.service import AuthService
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)
from bai_scenario.runner.unwired import unwired
from bai_scenario.valkey import ScenarioValkey


def _registry(
    engine: Any, validators: V2ActionValidators, monitors: ActionMonitors
) -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )


def _key_pool() -> KeyProviderPool:
    return KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN)


@pytest.fixture
async def adapter(
    engine: Any,
    config: ManagerConfigProvider,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    valkey: ScenarioValkey,
) -> UserAdapter:
    provider = V2DBOpsProvider(engine)
    registry = _registry(engine, validators, monitors)
    key_pool = _key_pool()
    user = UserProcessors(
        registry.group(GroupMeta(UserEntityType())),
        UserService(
            unwired(StorageSessionManager, "only purging a user with folders reaches it"),
            valkey.stat,
            unwired(AgentRegistry, "no user operation reaches the agents"),
            UserRepository(
                engine,
                provider,
                ShareOpsProvider(engine),
                ResourcePolicyOpsProvider(engine),
                key_pool,
            ),
            unwired(SchedulingController, "only purging a user with sessions reaches it"),
        ),
    )
    domain = DomainProcessors(
        registry.group(GroupMeta(DomainEntityType())),
        DomainService(DomainRepository(engine, DomainOpsProvider(engine))),
    )
    return UserAdapter(user, domain, config.config.auth, key_pool)


@pytest.fixture
async def auth(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
    valkey: ScenarioValkey,
) -> AuthProcessors:
    registry = _registry(engine, validators, monitors)
    key_pool = _key_pool()
    return AuthProcessors(
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
            unwired(SSHKeyValidator, "only uploading an SSH key validates one"),
            ClientIPMaskingRepository(engine),
            key_pool,
        ),
    )


@pytest.fixture
async def login_session_adapter(auth: AuthProcessors) -> LoginSessionAdapter:
    return LoginSessionAdapter(auth)


@pytest.fixture
async def login_history_adapter(auth: AuthProcessors) -> LoginHistoryAdapter:
    return LoginHistoryAdapter(auth)
