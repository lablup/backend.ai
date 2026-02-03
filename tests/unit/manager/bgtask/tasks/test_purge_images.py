from __future__ import annotations

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.bgtask.tasks.purge_images import (
    PurgeAgentSpec,
    PurgedImageData,
    PurgeImagesHandler,
    PurgeImagesManifest,
    PurgeImageSpec,
    PurgeImagesTaskResult,
)
from ai.backend.manager.bgtask.types import ManagerBgtaskName


class TestPurgeImagesHandler:
    """Tests for PurgeImagesHandler, PurgeImagesManifest, and PurgeImagesTaskResult."""

    @pytest.fixture
    def sample_agent_spec(self) -> PurgeAgentSpec:
        """Sample agent spec for testing."""
        return PurgeAgentSpec(
            agent_id=AgentId("agent-123"),
            images=[
                PurgeImageSpec(
                    name="test-image:latest",
                    registry="docker.io",
                    architecture="x86_64",
                )
            ],
        )

    @pytest.fixture
    def sample_purged_image(self) -> PurgedImageData:
        """Sample purged image data."""
        return PurgedImageData(
            agent_id="agent-123",
            image_name="test-image:latest",
            reserved_bytes=1024 * 1024 * 100,  # 100MB
        )

    def test_handler_name(self) -> None:
        """Test handler returns correct name."""
        assert PurgeImagesHandler.name() == ManagerBgtaskName.PURGE_IMAGES

    def test_handler_manifest_type(self) -> None:
        """Test handler returns correct manifest type."""
        assert PurgeImagesHandler.manifest_type() == PurgeImagesManifest

    def test_manifest_creation(self, sample_agent_spec: PurgeAgentSpec) -> None:
        """Test manifest can be created with agent specs."""
        manifest = PurgeImagesManifest(
            keys=[sample_agent_spec],
            force=True,
            noprune=False,
        )
        assert len(manifest.keys) == 1
        assert manifest.force is True
        assert manifest.noprune is False

    def test_manifest_serialization(self, sample_agent_spec: PurgeAgentSpec) -> None:
        """Test manifest can be serialized and deserialized."""
        manifest = PurgeImagesManifest(
            keys=[sample_agent_spec],
            force=False,
            noprune=True,
        )

        # Serialize to dict
        data = manifest.model_dump(mode="json")
        assert len(data["keys"]) == 1
        assert data["keys"][0]["agent_id"] == "agent-123"
        assert data["force"] is False
        assert data["noprune"] is True

        # Deserialize back
        restored = PurgeImagesManifest.model_validate(data)
        assert len(restored.keys) == 1
        assert restored.keys[0].agent_id == AgentId("agent-123")
        assert restored.force is False
        assert restored.noprune is True

    def test_result_success_serialization(self, sample_purged_image: PurgedImageData) -> None:
        """Test result can be serialized and deserialized with success case."""
        result = PurgeImagesTaskResult(
            total_reserved_bytes=1024 * 1024 * 100,
            purged_images=[sample_purged_image],
            errors=[],
        )

        # Serialize to dict
        data = result.model_dump(mode="json")
        assert data["total_reserved_bytes"] == 1024 * 1024 * 100
        assert len(data["purged_images"]) == 1
        assert data["purged_images"][0]["agent_id"] == "agent-123"
        assert data["errors"] == []

        # Deserialize back
        restored = PurgeImagesTaskResult.model_validate(data)
        assert restored.total_reserved_bytes == 1024 * 1024 * 100
        assert len(restored.purged_images) == 1
        assert restored.purged_images[0].agent_id == "agent-123"
        assert restored.errors == []

    def test_result_with_errors_serialization(self) -> None:
        """Test result can be serialized and deserialized with errors."""
        result = PurgeImagesTaskResult(
            total_reserved_bytes=0,
            purged_images=[],
            errors=["Failed to connect to agent", "Image not found"],
        )

        # Serialize to dict
        data = result.model_dump(mode="json")
        assert data["total_reserved_bytes"] == 0
        assert data["purged_images"] == []
        assert len(data["errors"]) == 2

        # Deserialize back
        restored = PurgeImagesTaskResult.model_validate(data)
        assert restored.total_reserved_bytes == 0
        assert restored.purged_images == []
        assert len(restored.errors) == 2
