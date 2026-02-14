"""Tests for registry domain response DTOs."""

import uuid

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.dto.manager.registry.response import (
    DeleteArtifactResponse,
    ImportArtifactResponse,
    PatchContainerRegistryResponseModel,
    RegistryQuotaResponse,
    UpdateArtifactResponse,
)


class TestContainerRegistryResponseModels:
    def test_patch_container_registry_response_model(self) -> None:
        uid = uuid.uuid4()
        model = PatchContainerRegistryResponseModel(
            id=uid,
            url="https://registry.example.com",
            registry_name="test-registry",
            type=ContainerRegistryType.DOCKER,
        )
        assert model.id == uid
        assert model.url == "https://registry.example.com"

    def test_patch_container_registry_response_serialization(self) -> None:
        uid = uuid.uuid4()
        model = PatchContainerRegistryResponseModel(
            id=uid,
            url="https://registry.example.com",
        )
        json_data = model.model_dump_json()
        assert isinstance(json_data, str)
        restored = PatchContainerRegistryResponseModel.model_validate_json(json_data)
        assert restored.id == model.id
        assert restored.url == model.url


class TestArtifactResponseModels:
    def test_import_artifact_response(self) -> None:
        model = ImportArtifactResponse(
            artifact_id="art-123",
            name="test-artifact",
            version="1.0.0",
            size=1024,
        )
        assert model.artifact_id == "art-123"
        assert model.name == "test-artifact"
        assert model.size == 1024

    def test_update_artifact_response(self) -> None:
        model = UpdateArtifactResponse(
            artifact_id="art-123",
            name="test-artifact",
            version="2.0.0",
        )
        assert model.artifact_id == "art-123"
        assert model.version == "2.0.0"

    def test_delete_artifact_response(self) -> None:
        model = DeleteArtifactResponse(
            artifact_id="art-123",
            message="Artifact deleted successfully",
        )
        assert model.artifact_id == "art-123"
        assert model.message == "Artifact deleted successfully"


class TestRegistryQuotaResponse:
    def test_registry_quota_response(self) -> None:
        model = RegistryQuotaResponse(result=100)
        assert model.result == 100

    def test_registry_quota_response_none(self) -> None:
        model = RegistryQuotaResponse()
        assert model.result is None

    def test_registry_quota_response_serialization(self) -> None:
        model = RegistryQuotaResponse(result=50)
        json_data = model.model_dump_json()
        assert isinstance(json_data, str)
        restored = RegistryQuotaResponse.model_validate_json(json_data)
        assert restored.result == 50

    def test_registry_quota_response_schema(self) -> None:
        schema = RegistryQuotaResponse.model_json_schema()
        assert "result" in schema["properties"]
