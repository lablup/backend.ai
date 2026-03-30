from __future__ import annotations

import uuid

import pytest

from ai.backend.common.data.session.types import CustomizedImageVisibilityScope
from ai.backend.common.types import SessionId
from ai.backend.manager.bgtask.tasks.commit_session import (
    CommitSessionHandler,
    CommitSessionManifest,
    CommitSessionResult,
)
from ai.backend.manager.bgtask.types import ManagerBgtaskName


class TestCommitSessionHandler:
    """Tests for CommitSessionHandler and CommitSessionManifest."""

    @pytest.fixture
    def sample_session_id(self) -> SessionId:
        """Sample session ID for testing."""
        return SessionId(uuid.uuid4())

    @pytest.fixture
    def sample_manifest(self, sample_session_id: SessionId) -> CommitSessionManifest:
        """Sample manifest for testing."""
        return CommitSessionManifest(
            session_id=sample_session_id,
            registry_hostname="registry.example.com",
            registry_project="test-project",
            image_name="test-image",
            image_visibility=CustomizedImageVisibilityScope.USER,
            image_owner_id="user-123",
            user_email="test@example.com",
        )

    def test_handler_name(self) -> None:
        """Test handler returns correct name."""
        assert CommitSessionHandler.name() == ManagerBgtaskName.COMMIT_SESSION

    def test_handler_manifest_type(self) -> None:
        """Test handler returns correct manifest type."""
        assert CommitSessionHandler.manifest_type() == CommitSessionManifest

    def test_manifest_creation(self, sample_session_id: SessionId) -> None:
        """Test manifest can be created with required fields."""
        manifest = CommitSessionManifest(
            session_id=sample_session_id,
            registry_hostname="registry.example.com",
            registry_project="test-project",
            image_name="test-image",
            image_visibility=CustomizedImageVisibilityScope.USER,
            image_owner_id="user-123",
            user_email="test@example.com",
        )
        assert manifest.session_id == sample_session_id
        assert manifest.registry_hostname == "registry.example.com"
        assert manifest.registry_project == "test-project"
        assert manifest.image_name == "test-image"
        assert manifest.image_visibility == CustomizedImageVisibilityScope.USER
        assert manifest.image_owner_id == "user-123"
        assert manifest.user_email == "test@example.com"

    def test_manifest_serialization(self, sample_manifest: CommitSessionManifest) -> None:
        """Test manifest can be serialized and deserialized."""
        # Serialize to dict
        data = sample_manifest.model_dump(mode="json")
        assert data["session_id"] == str(sample_manifest.session_id)
        assert data["registry_hostname"] == sample_manifest.registry_hostname
        assert data["registry_project"] == sample_manifest.registry_project
        assert data["image_name"] == sample_manifest.image_name

        # Deserialize back
        restored = CommitSessionManifest.model_validate(data)
        assert restored.session_id == sample_manifest.session_id
        assert restored.registry_hostname == sample_manifest.registry_hostname
        assert restored.image_visibility == sample_manifest.image_visibility

    def test_result_default_values(self) -> None:
        """Test result default values are None."""
        result = CommitSessionResult()
        assert result.image_id is None
        assert result.error_message is None

    def test_result_success_serialization(self) -> None:
        """Test result can be serialized and deserialized with success case."""
        image_id = uuid.uuid4()
        result = CommitSessionResult(image_id=image_id, error_message=None)

        # Serialize to dict
        data = result.model_dump(mode="json")
        assert data["image_id"] == str(image_id)
        assert data["error_message"] is None

        # Deserialize back
        restored = CommitSessionResult.model_validate(data)
        assert restored.image_id == image_id
        assert restored.error_message is None

    def test_result_error_serialization(self) -> None:
        """Test result can be serialized and deserialized with error case."""
        error_msg = "Session not found"
        result = CommitSessionResult(image_id=None, error_message=error_msg)

        # Serialize to dict
        data = result.model_dump(mode="json")
        assert data["image_id"] is None
        assert data["error_message"] == error_msg

        # Deserialize back
        restored = CommitSessionResult.model_validate(data)
        assert restored.image_id is None
        assert restored.error_message == error_msg
