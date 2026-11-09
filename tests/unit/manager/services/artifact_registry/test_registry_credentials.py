from __future__ import annotations

from dataclasses import dataclass, replace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.huggingface_registry.types import (
    HuggingFaceRegistryConnectionData,
    HuggingFaceRegistryData,
)
from ai.backend.manager.data.reservoir_registry.types import (
    ReservoirRegistryConnectionData,
    ReservoirRegistryData,
)
from ai.backend.manager.defs import SECRET_KEY_PLACEHOLDER, TOKEN_PLACEHOLDER
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.repositories.artifact_registry.repository import ArtifactRegistryRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.bulk_get import (
    BulkGetHuggingFaceRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.huggingface.get import (
    GetHuggingFaceRegistryAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.bulk_get import (
    BulkGetReservoirRegistriesAction,
)
from ai.backend.manager.services.artifact_registry.actions.reservoir.get import (
    GetReservoirRegistryAction,
)
from ai.backend.manager.services.artifact_registry.service import ArtifactRegistryService

_REGISTRY_ID = ArtifactRegistryID(uuid4())
_STORED_RESERVOIR_REGISTRY = ReservoirRegistryData(
    id=_REGISTRY_ID,
    name="reservoir",
    endpoint="https://reservoir.example.com",
    access_key="access-key",
    secret_key="stored-secret-key",
    api_version="v1",
)
_STORED_RESERVOIR_CONNECTION = ReservoirRegistryConnectionData(
    id=_REGISTRY_ID,
    endpoint="https://reservoir.example.com",
    access_key="access-key",
    secret_key="stored-secret-key",
    api_version="v1",
)
_STORED_TOKEN = "stored-token"


@dataclass(frozen=True)
class _SecretKeyCase:
    role: UserRole
    expected_secret_key: str


@dataclass(frozen=True)
class _TokenCase:
    role: UserRole
    stored_token: str | None
    expected_token: str | None


@dataclass(frozen=True)
class _HuggingFaceRegistryStored:
    service: ArtifactRegistryService
    registry: HuggingFaceRegistryData
    connection: HuggingFaceRegistryConnectionData


class TestReservoirRegistrySecretKey:
    @pytest.fixture
    def caller_role(self, case: _SecretKeyCase) -> UserRole:
        return case.role

    @pytest.fixture
    def service_holding_a_reservoir_registry(self) -> ArtifactRegistryService:
        reservoir_repository = MagicMock(spec=ReservoirRegistryRepository)
        reservoir_repository.get_reservoir_registry_data_by_id = AsyncMock(
            return_value=_STORED_RESERVOIR_REGISTRY
        )
        reservoir_repository.registry_connections = AsyncMock(
            return_value={_REGISTRY_ID: _STORED_RESERVOIR_CONNECTION}
        )
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    @pytest.mark.parametrize(
        "case",
        [
            _SecretKeyCase(role=UserRole.SUPERADMIN, expected_secret_key="stored-secret-key"),
            _SecretKeyCase(role=UserRole.MONITOR, expected_secret_key=SECRET_KEY_PLACEHOLDER),
            _SecretKeyCase(role=UserRole.ADMIN, expected_secret_key=SECRET_KEY_PLACEHOLDER),
            _SecretKeyCase(role=UserRole.USER, expected_secret_key=SECRET_KEY_PLACEHOLDER),
        ],
        ids=lambda case: case.role.value,
    )
    async def test_get_returns_the_stored_secret_key_only_to_a_superadmin(
        self,
        case: _SecretKeyCase,
        service_holding_a_reservoir_registry: ArtifactRegistryService,
    ) -> None:
        result = await service_holding_a_reservoir_registry.get_reservoir_registry(
            GetReservoirRegistryAction(registry_id=_REGISTRY_ID, reservoir_id=_REGISTRY_ID)
        )

        assert result.result == replace(
            _STORED_RESERVOIR_REGISTRY, secret_key=case.expected_secret_key
        )

    @pytest.mark.parametrize(
        "case",
        [
            _SecretKeyCase(role=UserRole.SUPERADMIN, expected_secret_key="stored-secret-key"),
            _SecretKeyCase(role=UserRole.MONITOR, expected_secret_key=SECRET_KEY_PLACEHOLDER),
            _SecretKeyCase(role=UserRole.ADMIN, expected_secret_key=SECRET_KEY_PLACEHOLDER),
            _SecretKeyCase(role=UserRole.USER, expected_secret_key=SECRET_KEY_PLACEHOLDER),
        ],
        ids=lambda case: case.role.value,
    )
    async def test_bulk_get_returns_the_stored_secret_key_only_to_a_superadmin(
        self,
        case: _SecretKeyCase,
        service_holding_a_reservoir_registry: ArtifactRegistryService,
    ) -> None:
        result = await service_holding_a_reservoir_registry.bulk_get_reservoir_registries(
            BulkGetReservoirRegistriesAction(ids=[_REGISTRY_ID])
        )

        assert [item.value for item in result.items] == [
            replace(_STORED_RESERVOIR_CONNECTION, secret_key=case.expected_secret_key)
        ]


class TestHuggingFaceRegistryToken:
    @pytest.fixture
    def caller_role(self, case: _TokenCase) -> UserRole:
        return case.role

    @pytest.fixture
    def huggingface_registry_stored(self, case: _TokenCase) -> _HuggingFaceRegistryStored:
        registry = HuggingFaceRegistryData(
            id=_REGISTRY_ID,
            name="huggingface",
            url="https://huggingface.co",
            token=case.stored_token,
        )
        connection = HuggingFaceRegistryConnectionData(
            id=_REGISTRY_ID,
            url="https://huggingface.co",
            token=case.stored_token,
        )
        huggingface_repository = MagicMock(spec=HuggingFaceRepository)
        huggingface_repository.get_registry_data_by_id = AsyncMock(return_value=registry)
        huggingface_repository.registry_connections = AsyncMock(
            return_value={_REGISTRY_ID: connection}
        )
        return _HuggingFaceRegistryStored(
            service=ArtifactRegistryService(
                huggingface_registry_repository=huggingface_repository,
                reservoir_repository=MagicMock(spec=ReservoirRegistryRepository),
                artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
            ),
            registry=registry,
            connection=connection,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _TokenCase(
                role=UserRole.SUPERADMIN, stored_token=_STORED_TOKEN, expected_token=_STORED_TOKEN
            ),
            _TokenCase(
                role=UserRole.MONITOR, stored_token=_STORED_TOKEN, expected_token=TOKEN_PLACEHOLDER
            ),
            _TokenCase(
                role=UserRole.ADMIN, stored_token=_STORED_TOKEN, expected_token=TOKEN_PLACEHOLDER
            ),
            _TokenCase(
                role=UserRole.USER, stored_token=_STORED_TOKEN, expected_token=TOKEN_PLACEHOLDER
            ),
            _TokenCase(role=UserRole.USER, stored_token=None, expected_token=None),
        ],
        ids=["superadmin", "monitor", "admin", "user", "user-reading-a-registry-without-a-token"],
    )
    async def test_get_returns_the_stored_token_only_to_a_superadmin(
        self,
        case: _TokenCase,
        huggingface_registry_stored: _HuggingFaceRegistryStored,
    ) -> None:
        result = await huggingface_registry_stored.service.get_huggingface_registry(
            GetHuggingFaceRegistryAction(registry_id=_REGISTRY_ID)
        )

        assert result.result == replace(
            huggingface_registry_stored.registry, token=case.expected_token
        )

    @pytest.mark.parametrize(
        "case",
        [
            _TokenCase(
                role=UserRole.SUPERADMIN, stored_token=_STORED_TOKEN, expected_token=_STORED_TOKEN
            ),
            _TokenCase(
                role=UserRole.MONITOR, stored_token=_STORED_TOKEN, expected_token=TOKEN_PLACEHOLDER
            ),
            _TokenCase(
                role=UserRole.ADMIN, stored_token=_STORED_TOKEN, expected_token=TOKEN_PLACEHOLDER
            ),
            _TokenCase(
                role=UserRole.USER, stored_token=_STORED_TOKEN, expected_token=TOKEN_PLACEHOLDER
            ),
            _TokenCase(role=UserRole.USER, stored_token=None, expected_token=None),
        ],
        ids=["superadmin", "monitor", "admin", "user", "user-reading-a-registry-without-a-token"],
    )
    async def test_bulk_get_returns_the_stored_token_only_to_a_superadmin(
        self,
        case: _TokenCase,
        huggingface_registry_stored: _HuggingFaceRegistryStored,
    ) -> None:
        result = await huggingface_registry_stored.service.bulk_get_huggingface_registries(
            BulkGetHuggingFaceRegistriesAction(ids=[_REGISTRY_ID])
        )

        assert [item.value for item in result.items] == [
            replace(huggingface_registry_stored.connection, token=case.expected_token)
        ]


class TestBulkGetOfAnAbsentRegistry:
    @pytest.fixture
    def service_holding_no_reservoir_registry(self) -> ArtifactRegistryService:
        reservoir_repository = MagicMock(spec=ReservoirRegistryRepository)
        reservoir_repository.registry_connections = AsyncMock(return_value={})
        return ArtifactRegistryService(
            huggingface_registry_repository=MagicMock(spec=HuggingFaceRepository),
            reservoir_repository=reservoir_repository,
            artifact_registry_repository=MagicMock(spec=ArtifactRegistryRepository),
        )

    async def test_an_absent_id_fails_as_not_found(
        self, service_holding_no_reservoir_registry: ArtifactRegistryService
    ) -> None:
        result = await service_holding_no_reservoir_registry.bulk_get_reservoir_registries(
            BulkGetReservoirRegistriesAction(ids=[_REGISTRY_ID])
        )

        assert [type(item.error) for item in result.items] == [EntityNotFoundError]
