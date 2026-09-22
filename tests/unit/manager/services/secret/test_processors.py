from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.common.data.entity.secret import SecretFieldType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    FieldGroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.global_scope.validator.rbac import (
    VirtualEntityGlobalActionRBACValidator,
)
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.data.permission.global_entity import GlobalEntityIDCache
from ai.backend.manager.data.secret.types import (
    KeyProviderType,
    SecretFieldData,
    SecretStatus,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.secret.repository import SecretRepository
from ai.backend.manager.services.secret.actions.reencrypt import ReencryptSecretsAction
from ai.backend.manager.services.secret.actions.status import GetSecretStatusAction
from ai.backend.manager.services.secret.processors import SecretProcessors
from ai.backend.manager.services.secret.service import SecretService


@pytest.fixture
def repository() -> MagicMock:
    repository = MagicMock(spec=SecretRepository)
    status = SecretStatus(write_provider_type=KeyProviderType.PLAIN, counts=[])
    repository.status.return_value = status
    return repository


@pytest.fixture(autouse=True)
def global_singleton() -> Iterator[None]:
    GlobalEntityIDCache.fill({name: GlobalEntityID(uuid.uuid4()) for name in GlobalEntityName})
    try:
        yield
    finally:
        GlobalEntityIDCache.clear()


@pytest.fixture
def global_gate() -> VirtualEntityGlobalActionRBACValidator:
    """The production gate over a graph granting nothing, so only the roles pass."""
    permission_check = MagicMock(spec=RbacPermissionCheckRepository)
    permission_check.governed_permissions = AsyncMock(
        side_effect=lambda keys: dict.fromkeys(keys, Permission.NONE)
    )
    config_provider = MagicMock()
    config_provider.config.manager.rbac.enforcement_enabled = True
    return VirtualEntityGlobalActionRBACValidator(permission_check, config_provider)


@pytest.fixture
def registry(global_gate: VirtualEntityGlobalActionRBACValidator) -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(global_scope=[global_gate]),
            repository=OpsRepository(MagicMock()),
        )
    )


@pytest.fixture
def processors(registry: ProcessorRegistry[Any], repository: MagicMock) -> SecretProcessors:
    return SecretProcessors(
        registry.concern(ConcernMeta(Concern.SYSTEM)).dangling_field_group(
            FieldGroupMeta(SecretFieldType()), SecretFieldData
        ),
        SecretService(repository),
    )


@pytest.fixture
def superadmin() -> UserData:
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=True,
        is_superadmin=True,
        role=UserRole.SUPERADMIN,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture(params=[UserRole.USER, UserRole.ADMIN])
def non_superadmin(request: pytest.FixtureRequest, superadmin: UserData) -> UserData:
    return dataclasses.replace(
        superadmin,
        is_admin=request.param == UserRole.ADMIN,
        is_superadmin=False,
        role=request.param,
    )


@pytest.fixture
def monitor_user(superadmin: UserData) -> UserData:
    return dataclasses.replace(
        superadmin, is_admin=False, is_superadmin=False, role=UserRole.MONITOR
    )


class TestGetSecretStatus:
    async def test_refuses_non_superadmin(
        self,
        processors: SecretProcessors,
        repository: MagicMock,
        non_superadmin: UserData,
    ) -> None:
        with with_user(non_superadmin), pytest.raises(InsufficientPrivilege):
            await processors.get_status.run(GetSecretStatusAction())
        repository.status.assert_not_awaited()

    async def test_allows_monitor_to_read_status(
        self,
        processors: SecretProcessors,
        repository: MagicMock,
        monitor_user: UserData,
    ) -> None:
        with with_user(monitor_user):
            result = await processors.get_status.run(GetSecretStatusAction())
        assert result.status == repository.status.return_value


class TestReencryptSecrets:
    async def test_refuses_non_superadmin(
        self,
        processors: SecretProcessors,
        repository: MagicMock,
        non_superadmin: UserData,
    ) -> None:
        with with_user(non_superadmin), pytest.raises(InsufficientPrivilege):
            await processors.reencrypt.run(ReencryptSecretsAction())
        repository.reencrypt.assert_not_awaited()

    async def test_refuses_monitor_reencryption(
        self,
        processors: SecretProcessors,
        repository: MagicMock,
        monitor_user: UserData,
    ) -> None:
        with with_user(monitor_user), pytest.raises(InsufficientPrivilege):
            await processors.reencrypt.run(ReencryptSecretsAction())
        repository.reencrypt.assert_not_awaited()
