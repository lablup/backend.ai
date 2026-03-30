"""Tests for ai.backend.common.dto.manager.v2.artifact.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from ai.backend.common.data.artifact.types import (
    ArtifactRevisionDownloadProgress,
    CombinedDownloadProgress,
    DownloadProgressData,
)
from ai.backend.common.dto.manager.v2.artifact.response import (
    ApproveRevisionPayload,
    ArtifactNode,
    ArtifactRevisionImportTaskInfo,
    ArtifactRevisionNode,
    CancelImportTaskPayload,
    CleanupRevisionsPayload,
    GetRevisionDownloadProgressPayload,
    GetRevisionReadmePayload,
    ImportArtifactsPayload,
    RejectRevisionPayload,
    UpdateArtifactPayload,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactRegistryType,
    ArtifactStatus,
    ArtifactType,
)


def _make_revision_node(
    status: ArtifactStatus = ArtifactStatus.AVAILABLE,
) -> ArtifactRevisionNode:
    now = datetime.now(tz=UTC)
    return ArtifactRevisionNode(
        id=uuid.uuid4(),
        artifact_id=uuid.uuid4(),
        version="v1.0",
        status=status,
        created_at=now,
        updated_at=now,
    )


def _make_artifact_node() -> ArtifactNode:
    now = datetime.now(tz=UTC)
    return ArtifactNode(
        id=uuid.uuid4(),
        name="test-model",
        type=ArtifactType.MODEL,
        registry_id=uuid.uuid4(),
        source_registry_id=uuid.uuid4(),
        registry_type=ArtifactRegistryType.HUGGINGFACE,
        source_registry_type=ArtifactRegistryType.HUGGINGFACE,
        availability=ArtifactAvailability.ALIVE,
        scanned_at=now,
        updated_at=now,
        readonly=False,
    )


class TestArtifactRevisionNode:
    """Tests for ArtifactRevisionNode model creation."""

    def test_basic_creation(self) -> None:
        node = _make_revision_node()
        assert node.version == "v1.0"
        assert node.status == ArtifactStatus.AVAILABLE

    def test_optional_fields_default_to_none(self) -> None:
        node = _make_revision_node()
        assert node.size is None
        assert node.remote_status is None
        assert node.digest is None
        assert node.verification_result is None

    def test_with_size(self) -> None:
        now = datetime.now(tz=UTC)
        node = ArtifactRevisionNode(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="v2.0",
            size="2048",
            status=ArtifactStatus.PULLED,
            created_at=now,
            updated_at=now,
        )
        assert node.size == "2048"

    def test_serialization_round_trip(self) -> None:
        node = _make_revision_node()
        json_str = node.model_dump_json()
        restored = ArtifactRevisionNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.version == node.version
        assert restored.status == node.status

    def test_json_contains_status_string(self) -> None:
        node = _make_revision_node(status=ArtifactStatus.FAILED)
        parsed = json.loads(node.model_dump_json())
        assert parsed["status"] == "FAILED"


class TestArtifactNode:
    """Tests for ArtifactNode model creation."""

    def test_basic_creation(self) -> None:
        node = _make_artifact_node()
        assert node.name == "test-model"
        assert node.type == ArtifactType.MODEL
        assert node.readonly is False

    def test_optional_fields_default(self) -> None:
        node = _make_artifact_node()
        assert node.description is None
        assert node.extra is None
        assert node.revisions == []

    def test_with_revisions(self) -> None:
        now = datetime.now(tz=UTC)
        rev = ArtifactRevisionNode(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="v1.0",
            status=ArtifactStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
        )
        node = _make_artifact_node()
        node_with_revisions = node.model_copy(update={"revisions": [rev]})
        assert len(node_with_revisions.revisions) == 1

    def test_serialization_round_trip(self) -> None:
        node = _make_artifact_node()
        json_str = node.model_dump_json()
        restored = ArtifactNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.name == node.name
        assert restored.type == node.type
        assert restored.availability == ArtifactAvailability.ALIVE

    def test_json_contains_type_string(self) -> None:
        node = _make_artifact_node()
        parsed = json.loads(node.model_dump_json())
        assert parsed["type"] == "MODEL"
        assert parsed["availability"] == "ALIVE"


class TestArtifactRevisionImportTaskInfo:
    """Tests for ArtifactRevisionImportTaskInfo model."""

    def test_creation_with_task_id(self) -> None:
        rev_node = _make_revision_node()
        info = ArtifactRevisionImportTaskInfo(
            task_id="task-123",
            artifact_revision=rev_node,
        )
        assert info.task_id == "task-123"
        assert info.artifact_revision.version == "v1.0"

    def test_task_id_defaults_to_none(self) -> None:
        rev_node = _make_revision_node()
        info = ArtifactRevisionImportTaskInfo(artifact_revision=rev_node)
        assert info.task_id is None

    def test_round_trip_serialization(self) -> None:
        rev_node = _make_revision_node()
        info = ArtifactRevisionImportTaskInfo(task_id="task-456", artifact_revision=rev_node)
        json_str = info.model_dump_json()
        restored = ArtifactRevisionImportTaskInfo.model_validate_json(json_str)
        assert restored.task_id == "task-456"
        assert restored.artifact_revision.id == rev_node.id


class TestUpdateArtifactPayload:
    """Tests for UpdateArtifactPayload model."""

    def test_creation_with_artifact_node(self) -> None:
        node = _make_artifact_node()
        payload = UpdateArtifactPayload(artifact=node)
        assert payload.artifact.name == "test-model"

    def test_round_trip_serialization(self) -> None:
        node = _make_artifact_node()
        payload = UpdateArtifactPayload(artifact=node)
        json_str = payload.model_dump_json()
        restored = UpdateArtifactPayload.model_validate_json(json_str)
        assert restored.artifact.id == node.id
        assert restored.artifact.name == node.name


class TestImportArtifactsPayload:
    """Tests for ImportArtifactsPayload model."""

    def test_creation_with_tasks(self) -> None:
        rev_node = _make_revision_node()
        task_info = ArtifactRevisionImportTaskInfo(task_id="t1", artifact_revision=rev_node)
        payload = ImportArtifactsPayload(tasks=[task_info])
        assert len(payload.tasks) == 1

    def test_empty_tasks_list(self) -> None:
        payload = ImportArtifactsPayload(tasks=[])
        assert payload.tasks == []

    def test_round_trip_serialization(self) -> None:
        rev_node = _make_revision_node()
        task_info = ArtifactRevisionImportTaskInfo(task_id="t1", artifact_revision=rev_node)
        payload = ImportArtifactsPayload(tasks=[task_info])
        json_str = payload.model_dump_json()
        restored = ImportArtifactsPayload.model_validate_json(json_str)
        assert len(restored.tasks) == 1
        assert restored.tasks[0].task_id == "t1"


class TestCleanupRevisionsPayload:
    """Tests for CleanupRevisionsPayload model."""

    def test_creation_with_revisions(self) -> None:
        rev_node = _make_revision_node()
        payload = CleanupRevisionsPayload(artifact_revisions=[rev_node])
        assert len(payload.artifact_revisions) == 1

    def test_empty_revisions_list(self) -> None:
        payload = CleanupRevisionsPayload(artifact_revisions=[])
        assert payload.artifact_revisions == []

    def test_round_trip_serialization(self) -> None:
        rev_node = _make_revision_node()
        payload = CleanupRevisionsPayload(artifact_revisions=[rev_node])
        json_str = payload.model_dump_json()
        restored = CleanupRevisionsPayload.model_validate_json(json_str)
        assert len(restored.artifact_revisions) == 1
        assert restored.artifact_revisions[0].id == rev_node.id


class TestApproveRevisionPayload:
    """Tests for ApproveRevisionPayload model."""

    def test_creation(self) -> None:
        rev_node = _make_revision_node(status=ArtifactStatus.AVAILABLE)
        payload = ApproveRevisionPayload(artifact_revision=rev_node)
        assert payload.artifact_revision.status == ArtifactStatus.AVAILABLE

    def test_round_trip_serialization(self) -> None:
        rev_node = _make_revision_node()
        payload = ApproveRevisionPayload(artifact_revision=rev_node)
        json_str = payload.model_dump_json()
        restored = ApproveRevisionPayload.model_validate_json(json_str)
        assert restored.artifact_revision.id == rev_node.id


class TestRejectRevisionPayload:
    """Tests for RejectRevisionPayload model."""

    def test_creation(self) -> None:
        rev_node = _make_revision_node(status=ArtifactStatus.REJECTED)
        payload = RejectRevisionPayload(artifact_revision=rev_node)
        assert payload.artifact_revision.status == ArtifactStatus.REJECTED

    def test_round_trip_serialization(self) -> None:
        rev_node = _make_revision_node(status=ArtifactStatus.REJECTED)
        payload = RejectRevisionPayload(artifact_revision=rev_node)
        json_str = payload.model_dump_json()
        restored = RejectRevisionPayload.model_validate_json(json_str)
        assert restored.artifact_revision.id == rev_node.id


class TestCancelImportTaskPayload:
    """Tests for CancelImportTaskPayload model."""

    def test_creation(self) -> None:
        rev_node = _make_revision_node()
        payload = CancelImportTaskPayload(artifact_revision=rev_node)
        assert payload.artifact_revision.id == rev_node.id

    def test_round_trip_serialization(self) -> None:
        rev_node = _make_revision_node()
        payload = CancelImportTaskPayload(artifact_revision=rev_node)
        json_str = payload.model_dump_json()
        restored = CancelImportTaskPayload.model_validate_json(json_str)
        assert restored.artifact_revision.id == rev_node.id


class TestGetRevisionReadmePayload:
    """Tests for GetRevisionReadmePayload model."""

    def test_creation_with_readme(self) -> None:
        payload = GetRevisionReadmePayload(readme="# My Model\nThis is a readme.")
        assert payload.readme == "# My Model\nThis is a readme."

    def test_readme_defaults_to_none(self) -> None:
        payload = GetRevisionReadmePayload()
        assert payload.readme is None

    def test_round_trip_serialization(self) -> None:
        payload = GetRevisionReadmePayload(readme="# README")
        json_str = payload.model_dump_json()
        restored = GetRevisionReadmePayload.model_validate_json(json_str)
        assert restored.readme == "# README"


class TestGetRevisionDownloadProgressPayload:
    """Tests for GetRevisionDownloadProgressPayload model."""

    def test_creation_with_progress(self) -> None:
        local_progress = ArtifactRevisionDownloadProgress(
            progress=DownloadProgressData(
                artifact_progress=None,
                file_progress=[],
            ),
            status="SCANNED",
        )
        combined = CombinedDownloadProgress(local=local_progress, remote=None)
        payload = GetRevisionDownloadProgressPayload(download_progress=combined)
        assert payload.download_progress is not None
        assert payload.download_progress.local.status == "SCANNED"

    def test_round_trip_serialization(self) -> None:
        local_progress = ArtifactRevisionDownloadProgress(
            progress=DownloadProgressData(
                artifact_progress=None,
                file_progress=[],
            ),
            status="AVAILABLE",
        )
        combined = CombinedDownloadProgress(local=local_progress, remote=None)
        payload = GetRevisionDownloadProgressPayload(download_progress=combined)
        json_str = payload.model_dump_json()
        restored = GetRevisionDownloadProgressPayload.model_validate_json(json_str)
        assert restored.download_progress.local.status == "AVAILABLE"
