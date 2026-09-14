from __future__ import annotations

import dataclasses
import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.secret import SecretFieldType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    FieldGroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.data.secret.types import (
    KeyProviderType,
    SecretFieldData,
    SecretStatus,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.repositories.ops.repository import OpsRepository
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


@pytest.fixture
def registry() -> ProcessorRegistry[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(),
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
