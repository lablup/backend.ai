from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.session.types import CustomizedImageVisibilityScope
from ai.backend.common.types import SessionId
from ai.backend.manager.bgtask.tasks.commit_session import (
    CommitSessionHandler,
    CommitSessionManifest,
    CommitSessionResult,
)
from ai.backend.manager.bgtask.types import ManagerBgtaskName
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.errors.kernel import SessionNotFound


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

    def test_result_success_serialization(self) -> None:
        """Test result can be serialized and deserialized with success case."""
        image_id = uuid.uuid4()
        result = CommitSessionResult(image_id=image_id)

        # Serialize to dict
        data = result.model_dump(mode="json")
        assert data["image_id"] == str(image_id)

        # Deserialize back
        restored = CommitSessionResult.model_validate(data)
        assert restored.image_id == image_id


class TestCommitSessionExecute:
    """Regression tests for CommitSessionHandler.execute() failure propagation.

    Previously execute() swallowed every failure into a success-typed
    CommitSessionResult, so the bgtask framework emitted bgtask_done and the
    WebUI reported a failed commit as successful.
    Failures must now raise domain exceptions so bgtask_failed is emitted
    (see PR #12168).
    """

    @pytest.fixture
    def sample_manifest(self) -> CommitSessionManifest:
        return CommitSessionManifest(
            session_id=SessionId(uuid.uuid4()),
            registry_hostname="registry.example.com",
            registry_project="test-project",
            image_name="test-image",
            image_visibility=CustomizedImageVisibilityScope.USER,
            image_owner_id="user-123",
            user_email="test@example.com",
        )

    def _make_handler(self, session_repository: AsyncMock) -> CommitSessionHandler:
        return CommitSessionHandler(
            session_repository=session_repository,
            image_repository=AsyncMock(),
            agent_registry=AsyncMock(),
            event_hub=MagicMock(),
            event_fetcher=MagicMock(),
        )

    async def test_missing_session_raises_session_not_found(
        self, sample_manifest: CommitSessionManifest
    ) -> None:
        session_repository = AsyncMock()
        session_repository.get_session_by_id.return_value = None
        handler = self._make_handler(session_repository)

        with pytest.raises(SessionNotFound):
            await handler.execute(sample_manifest)

    async def test_missing_registry_raises_container_registry_not_found(
        self, sample_manifest: CommitSessionManifest
    ) -> None:
        session_repository = AsyncMock()
        session_repository.get_session_by_id.return_value = MagicMock()
        session_repository.get_container_registry.return_value = None
        handler = self._make_handler(session_repository)

        with pytest.raises(ContainerRegistryNotFound):
            await handler.execute(sample_manifest)

    async def test_base_image_resolved_including_deleted(
        self, sample_manifest: CommitSessionManifest
    ) -> None:
        # A running session's base image may have been deleted, so the base
        # image must be resolved with alive_only=False (see PR #12168).
        session = MagicMock()
        session.main_kernel.image = "registry.example.com/base:latest"
        session.main_kernel.architecture = "x86_64"

        session_repository = AsyncMock()
        session_repository.get_session_by_id.return_value = session
        session_repository.get_container_registry.return_value = MagicMock()
        # Stop execution right after resolve_image so the test stays focused on
        # how the base image is resolved.
        session_repository.resolve_image.side_effect = RuntimeError("stop here")
        handler = self._make_handler(session_repository)

        with pytest.raises(RuntimeError):
            await handler.execute(sample_manifest)

        session_repository.resolve_image.assert_awaited_once()
        _, kwargs = session_repository.resolve_image.call_args
        assert kwargs["alive_only"] is False
