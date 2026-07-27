from __future__ import annotations

import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.vfolder.types import VFolderLocation, VFolderOwnershipType
from ai.backend.manager.errors.deployment import DeploymentDefinitionFileReadError
from ai.backend.manager.repositories.deployment.storage_source.storage_source import (
    DeploymentStorageSource,
)


@dataclass(frozen=True)
class AbsentFileCase:
    fetch_error: Exception | None
    content: bytes | None


@dataclass(frozen=True)
class MalformedDeploymentConfigCase:
    content: bytes


class TestDeploymentStorageSource:
    @pytest.fixture
    def vfolder_location(self) -> VFolderLocation:
        return VFolderLocation(
            id=uuid.uuid4(),
            quota_scope_id=None,
            host="local:volume",
            ownership_type=VFolderOwnershipType.USER,
            usage_mode=VFolderUsageMode.MODEL,
        )

    @pytest.fixture
    def fetch_file_content(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def deployment_storage_source(
        self,
        fetch_file_content: AsyncMock,
    ) -> DeploymentStorageSource:
        storage_manager = MagicMock(spec=StorageSessionManager)
        storage_manager.get_proxy_and_volume.return_value = ("local", "volume")
        manager_client = MagicMock()
        manager_client.fetch_file_content = fetch_file_content
        storage_manager.get_manager_facing_client.return_value = manager_client
        return DeploymentStorageSource(storage_manager)

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                AbsentFileCase(fetch_error=FileNotFoundError(), content=None), id="missing"
            ),
            pytest.param(AbsentFileCase(fetch_error=None, content=b""), id="empty"),
        ],
    )
    async def test_absent_file_returns_none(
        self,
        deployment_storage_source: DeploymentStorageSource,
        fetch_file_content: AsyncMock,
        vfolder_location: VFolderLocation,
        case: AbsentFileCase,
    ) -> None:
        fetch_file_content.side_effect = case.fetch_error
        fetch_file_content.return_value = case.content

        result = await deployment_storage_source.fetch_deployment_config(
            vfolder_location,
            ["deployment-config.yaml"],
        )

        assert result is None

    async def test_malformed_model_definition_raises_domain_error(
        self,
        deployment_storage_source: DeploymentStorageSource,
        fetch_file_content: AsyncMock,
        vfolder_location: VFolderLocation,
    ) -> None:
        fetch_file_content.return_value = b"models: [\n"

        with pytest.raises(DeploymentDefinitionFileReadError):
            await deployment_storage_source.fetch_model_definition(
                vfolder_location,
                ["model-definition.yaml"],
            )

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                MalformedDeploymentConfigCase(content=b"- item\n"),
                id="non-mapping",
            ),
            pytest.param(
                MalformedDeploymentConfigCase(content=b"environ: invalid\n"),
                id="schema-validation",
            ),
        ],
    )
    async def test_malformed_deployment_config_raises_domain_error(
        self,
        deployment_storage_source: DeploymentStorageSource,
        fetch_file_content: AsyncMock,
        vfolder_location: VFolderLocation,
        case: MalformedDeploymentConfigCase,
    ) -> None:
        fetch_file_content.return_value = case.content

        with pytest.raises(DeploymentDefinitionFileReadError):
            await deployment_storage_source.fetch_deployment_config(
                vfolder_location,
                ["deployment-config.yaml"],
            )
