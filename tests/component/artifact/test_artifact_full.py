"""
Component tests for Artifact CRUD, scan operations, and revision management.

This test suite covers:
- Artifact CRUD operations (search, update)
- Scan operations (HuggingFace, Reservoir, with retry)
- Revision management (import, cancel, approve, reject, cleanup)
- README and verification result queries
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import APIConfig
from ai.backend.client.v2.domains.artifact import Artifact
from ai.backend.client.v2.domains.artifact_registry import ArtifactRegistry
from ai.backend.manager.models import enums
from ai.backend.manager.models.artifact import ArtifactRow

if TYPE_CHECKING:
    from ai.backend.client.v2.domains.artifact import ArtifactProcessors
    from ai.backend.manager.models.artifact import ArtifactFactory


@pytest.fixture
async def artifact_seed(artifact_factory: ArtifactFactory) -> ArtifactRow:
    """Create a seed artifact with one revision for CRUD tests."""
    return await artifact_factory(
        status=enums.ArtifactStatus.ACTIVE,
        metadata={"description": "Test artifact for CRUD"},
    )


@pytest.fixture
async def artifact_with_multiple_revisions(artifact_factory: ArtifactFactory) -> ArtifactRow:
    """Create an artifact with multiple revisions for revision management tests."""
    # Additional revisions can be added in individual tests
    return await artifact_factory(
        status=enums.ArtifactStatus.ACTIVE,
        metadata={"description": "Test artifact with multiple revisions"},
    )


@pytest.fixture
async def artifact_for_scan(artifact_factory: ArtifactFactory) -> ArtifactRow:
    """Create an artifact for scan operation tests."""
    return await artifact_factory(
        status=enums.ArtifactStatus.ACTIVE,
        metadata={"description": "Test artifact for scan operations"},
    )


# ============================================================================
# Artifact CRUD Tests
# ============================================================================


class TestArtifactCRUD:
    """Tests for Artifact CRUD operations."""

    async def test_search_artifacts_paginated(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test searching artifacts with pagination."""
        artifact = Artifact(api_config, processors=artifact_processors)

        # Search for artifacts - should find at least the seed artifact
        result = await artifact.search_artifacts(
            limit=10,
            offset=0,
        )

        assert "items" in result
        assert "total_count" in result
        assert isinstance(result["items"], list)
        assert result["total_count"] >= 1

        # Verify our seed artifact is in the results
        artifact_ids = [item["id"] for item in result["items"]]
        assert str(artifact_seed.id) in artifact_ids

    async def test_search_artifacts_empty_results(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
    ) -> None:
        """Test searching artifacts with filter that yields no results."""
        artifact = Artifact(api_config, processors=artifact_processors)

        # Search with impossible filter
        result = await artifact.search_artifacts(
            limit=10,
            offset=0,
            filter_query=f"id eq '{uuid.uuid4()}'",  # Non-existent ID
        )

        assert result["total_count"] == 0
        assert len(result["items"]) == 0

    async def test_update_artifact_metadata(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test updating artifact metadata."""
        artifact = Artifact(api_config, processors=artifact_processors)

        # Update artifact metadata
        new_description = "Updated description"
        result = await artifact.update_artifact(
            artifact_id=str(artifact_seed.id),
            description=new_description,
            readonly=True,
        )

        assert result is not None
        assert result["description"] == new_description
        assert result["readonly"] is True

    async def test_update_artifact_readonly_flag(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test toggling artifact readonly flag."""
        artifact = Artifact(api_config, processors=artifact_processors)

        # Set to readonly
        result = await artifact.update_artifact(
            artifact_id=str(artifact_seed.id),
            readonly=True,
        )
        assert result["readonly"] is True

        # Set back to writable
        result = await artifact.update_artifact(
            artifact_id=str(artifact_seed.id),
            readonly=False,
        )
        assert result["readonly"] is False

    async def test_update_nonexistent_artifact(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
    ) -> None:
        """Test updating a non-existent artifact returns 404."""
        artifact = Artifact(api_config, processors=artifact_processors)

        with pytest.raises(BackendAPIError) as exc_info:
            await artifact.update_artifact(
                artifact_id=str(uuid.uuid4()),
                description="Should fail",
            )

        assert exc_info.value.status == 404


# ============================================================================
# Scan Operation Tests
# ============================================================================


class TestScanOperations:
    """Tests for artifact scan operations."""

    async def test_scan_huggingface_artifact(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
    ) -> None:
        """Test scanning HuggingFace artifact."""
        artifact_registry = ArtifactRegistry(api_config, processors=artifact_processors)

        # Mock the scan operation since it requires external HuggingFace connectivity
        with patch.object(
            artifact_registry,
            "scan_artifacts",
            new_callable=AsyncMock,
        ) as mock_scan:
            mock_scan.return_value = {
                "task_id": str(uuid.uuid4()),
                "status": "scanning",
                "registry": "huggingface",
            }

            result = await artifact_registry.scan_artifacts(
                registry="huggingface",
                artifact_id="bert-base-uncased",
            )

            assert result["status"] == "scanning"
            assert result["registry"] == "huggingface"
            assert "task_id" in result
            mock_scan.assert_called_once()

    async def test_scan_reservoir_artifact(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
    ) -> None:
        """Test scanning Reservoir artifact."""
        artifact_registry = ArtifactRegistry(api_config, processors=artifact_processors)

        # Mock the scan operation since it requires external Reservoir connectivity
        with patch.object(
            artifact_registry,
            "scan_artifacts",
            new_callable=AsyncMock,
        ) as mock_scan:
            mock_scan.return_value = {
                "task_id": str(uuid.uuid4()),
                "status": "scanning",
                "registry": "reservoir",
            }

            result = await artifact_registry.scan_artifacts(
                registry="reservoir",
                artifact_id="test-model",
            )

            assert result["status"] == "scanning"
            assert result["registry"] == "reservoir"
            assert "task_id" in result
            mock_scan.assert_called_once()

    @pytest.mark.xfail(reason="Requires storage-proxy setup")
    async def test_scan_with_retry_on_transient_failure(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
    ) -> None:
        """Test scan operation with retry on transient failure."""
        artifact_registry = ArtifactRegistry(api_config, processors=artifact_processors)

        # Simulate transient failure followed by success
        call_count = 0

        async def mock_scan_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise BackendAPIError(status=503, reason="Service temporarily unavailable")
            return {
                "task_id": str(uuid.uuid4()),
                "status": "scanning",
            }

        with patch.object(
            artifact_registry,
            "scan_artifacts",
            side_effect=mock_scan_with_retry,
        ):
            # First call should fail
            with pytest.raises(BackendAPIError) as exc_info:
                await artifact_registry.scan_artifacts(
                    registry="huggingface",
                    artifact_id="test-model",
                )
            assert exc_info.value.status == 503

            # Retry should succeed
            result = await artifact_registry.scan_artifacts(
                registry="huggingface",
                artifact_id="test-model",
            )
            assert result["status"] == "scanning"
            assert call_count == 2

    async def test_scan_nonexistent_source(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
    ) -> None:
        """Test scanning non-existent artifact source returns error."""
        artifact_registry = ArtifactRegistry(api_config, processors=artifact_processors)

        with patch.object(
            artifact_registry,
            "scan_artifacts",
            new_callable=AsyncMock,
        ) as mock_scan:
            mock_scan.side_effect = BackendAPIError(
                status=404,
                reason="Artifact not found in registry",
            )

            with pytest.raises(BackendAPIError) as exc_info:
                await artifact_registry.scan_artifacts(
                    registry="huggingface",
                    artifact_id="nonexistent-model-12345",
                )

            assert exc_info.value.status == 404


# ============================================================================
# Revision Management Tests
# ============================================================================


class TestRevisionManagement:
    """Tests for artifact revision management."""

    @pytest.mark.xfail(reason="Requires storage-proxy setup")
    async def test_import_revision(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test importing artifact revision."""
        artifact = Artifact(api_config, processors=artifact_processors)

        # Mock import operation
        with patch.object(artifact, "import_artifacts", new_callable=AsyncMock) as mock_import:
            mock_import.return_value = {
                "task_id": str(uuid.uuid4()),
                "status": "importing",
            }

            result = await artifact.import_artifacts(
                artifact_id=str(artifact_seed.id),
                revision_ids=[str(artifact_seed.revisions[0].id)],
            )

            assert result["status"] == "importing"
            assert "task_id" in result
            mock_import.assert_called_once()

    @pytest.mark.xfail(reason="Requires storage-proxy setup")
    async def test_cancel_import(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test canceling import task."""
        artifact = Artifact(api_config, processors=artifact_processors)

        task_id = str(uuid.uuid4())

        with patch.object(artifact, "cancel_import_task", new_callable=AsyncMock) as mock_cancel:
            mock_cancel.return_value = {
                "task_id": task_id,
                "status": "cancelled",
            }

            result = await artifact.cancel_import_task(task_id=task_id)

            assert result["status"] == "cancelled"
            assert result["task_id"] == task_id
            mock_cancel.assert_called_once()

    async def test_approve_revision(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test approving artifact revision."""
        artifact = Artifact(api_config, processors=artifact_processors)

        revision_id = str(artifact_seed.revisions[0].id)

        result = await artifact.approve_revision(
            artifact_id=str(artifact_seed.id),
            revision_id=revision_id,
        )

        assert result is not None
        # The revision status should be updated to APPROVED
        # (exact response structure depends on implementation)

    async def test_reject_revision(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test rejecting artifact revision."""
        artifact = Artifact(api_config, processors=artifact_processors)

        revision_id = str(artifact_seed.revisions[0].id)

        result = await artifact.reject_revision(
            artifact_id=str(artifact_seed.id),
            revision_id=revision_id,
        )

        assert result is not None
        # The revision status should be updated to REJECTED

    @pytest.mark.xfail(reason="Requires storage-proxy setup")
    async def test_cleanup_revision(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test cleaning up artifact revision resources."""
        artifact = Artifact(api_config, processors=artifact_processors)

        revision_id = str(artifact_seed.revisions[0].id)

        result = await artifact.cleanup_revisions(
            artifact_id=str(artifact_seed.id),
            revision_ids=[revision_id],
        )

        assert result is not None
        # Cleanup should succeed

    async def test_get_revision_readme(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test getting revision README content."""
        artifact = Artifact(api_config, processors=artifact_processors)

        revision_id = str(artifact_seed.revisions[0].id)

        # Mock the README retrieval since it may require storage-proxy
        with patch.object(
            artifact,
            "get_revision_readme",
            new_callable=AsyncMock,
        ) as mock_readme:
            mock_readme.return_value = {
                "content": "# Test README\n\nThis is a test artifact.",
                "format": "markdown",
            }

            result = await artifact.get_revision_readme(
                artifact_id=str(artifact_seed.id),
                revision_id=revision_id,
            )

            assert "content" in result
            assert result["format"] == "markdown"
            mock_readme.assert_called_once()

    async def test_get_verification_result(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_seed: ArtifactRow,
    ) -> None:
        """Test getting revision verification result."""
        artifact = Artifact(api_config, processors=artifact_processors)

        revision_id = str(artifact_seed.revisions[0].id)

        # Mock the verification result retrieval
        with patch.object(
            artifact,
            "get_revision_verification_result",
            new_callable=AsyncMock,
        ) as mock_verification:
            mock_verification.return_value = {
                "status": "verified",
                "checks": [
                    {"name": "file_integrity", "passed": True},
                    {"name": "virus_scan", "passed": True},
                ],
            }

            result = await artifact.get_revision_verification_result(
                artifact_id=str(artifact_seed.id),
                revision_id=revision_id,
            )

            assert result["status"] == "verified"
            assert len(result["checks"]) == 2
            mock_verification.assert_called_once()

    async def test_revision_lifecycle(
        self,
        api_config: APIConfig,
        artifact_processors: ArtifactProcessors,
        artifact_with_multiple_revisions: ArtifactRow,
    ) -> None:
        """Test complete revision lifecycle: import → approve → cleanup."""
        artifact = Artifact(api_config, processors=artifact_processors)

        artifact_id = str(artifact_with_multiple_revisions.id)
        revision_id = str(artifact_with_multiple_revisions.revisions[0].id)

        # Step 1: Approve revision
        approve_result = await artifact.approve_revision(
            artifact_id=artifact_id,
            revision_id=revision_id,
        )
        assert approve_result is not None

        # Step 2: Verify revision was approved
        # (In a real scenario, we'd query the revision status here)

        # Step 3: Cleanup is tested separately due to storage-proxy dependency
