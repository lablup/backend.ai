from __future__ import annotations

from ai.backend.manager.bgtask.tasks.rescan_images import (
    RescanImagesHandler,
    RescanImagesManifest,
    RescanImagesTaskResult,
)
from ai.backend.manager.bgtask.types import ManagerBgtaskName


class TestRescanImagesHandler:
    """Tests for RescanImagesHandler, RescanImagesManifest, and RescanImagesTaskResult."""

    def test_handler_name(self) -> None:
        """Test handler returns correct name."""
        assert RescanImagesHandler.name() == ManagerBgtaskName.RESCAN_IMAGES

    def test_handler_manifest_type(self) -> None:
        """Test handler returns correct manifest type."""
        assert RescanImagesHandler.manifest_type() == RescanImagesManifest

    def test_manifest_creation_all_registries(self) -> None:
        """Test manifest can be created to rescan all registries."""
        manifest = RescanImagesManifest(registry=None, project=None)
        assert manifest.registry is None
        assert manifest.project is None

    def test_manifest_creation_specific_registry(self) -> None:
        """Test manifest can be created for specific registry and project."""
        manifest = RescanImagesManifest(registry="docker.io", project="my-project")
        assert manifest.registry == "docker.io"
        assert manifest.project == "my-project"

    def test_manifest_serialization(self) -> None:
        """Test manifest can be serialized and deserialized."""
        manifest = RescanImagesManifest(registry="cr.backend.ai", project="stable")

        # Serialize to dict
        data = manifest.model_dump(mode="json")
        assert data["registry"] == "cr.backend.ai"
        assert data["project"] == "stable"

        # Deserialize back
        restored = RescanImagesManifest.model_validate(data)
        assert restored.registry == "cr.backend.ai"
        assert restored.project == "stable"

    def test_result_success_serialization(self) -> None:
        """Test result can be serialized and deserialized with success case."""
        result = RescanImagesTaskResult(
            rescanned_image_ids=["img-123", "img-456", "img-789"],
            errors=[],
        )

        # Serialize to dict
        data = result.model_dump(mode="json")
        assert len(data["rescanned_image_ids"]) == 3
        assert data["rescanned_image_ids"] == ["img-123", "img-456", "img-789"]
        assert data["errors"] == []

        # Deserialize back
        restored = RescanImagesTaskResult.model_validate(data)
        assert len(restored.rescanned_image_ids) == 3
        assert restored.rescanned_image_ids == ["img-123", "img-456", "img-789"]
        assert restored.errors == []

    def test_result_with_errors_serialization(self) -> None:
        """Test result can be serialized and deserialized with errors."""
        result = RescanImagesTaskResult(
            rescanned_image_ids=["img-123"],
            errors=["Failed to fetch image metadata", "Registry timeout"],
        )

        # Serialize to dict
        data = result.model_dump(mode="json")
        assert len(data["rescanned_image_ids"]) == 1
        assert len(data["errors"]) == 2
        assert data["errors"] == ["Failed to fetch image metadata", "Registry timeout"]

        # Deserialize back
        restored = RescanImagesTaskResult.model_validate(data)
        assert len(restored.rescanned_image_ids) == 1
        assert len(restored.errors) == 2
        assert restored.errors == ["Failed to fetch image metadata", "Registry timeout"]

    def test_result_empty_lists(self) -> None:
        """Test result with empty lists can be serialized."""
        result = RescanImagesTaskResult(
            rescanned_image_ids=[],
            errors=[],
        )

        # Serialize to dict
        data = result.model_dump(mode="json")
        assert data["rescanned_image_ids"] == []
        assert data["errors"] == []

        # Deserialize back
        restored = RescanImagesTaskResult.model_validate(data)
        assert restored.rescanned_image_ids == []
        assert restored.errors == []
