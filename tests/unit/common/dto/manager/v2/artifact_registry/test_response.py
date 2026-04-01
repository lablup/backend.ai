"""Tests for ai.backend.common.dto.manager.v2.artifact_registry.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.artifact.response import (
    ArtifactNode,
    ArtifactRevisionImportTaskInfo,
    ArtifactRevisionNode,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.common.dto.manager.v2.artifact_registry.response import (
    ArtifactRevisionDataNode,
    ArtifactWithRevisionsNode,
    DelegateImportArtifactsPayload,
    DelegateScanArtifactsPayload,
    RetrieveArtifactModelPayload,
    ScanArtifactModelsPayload,
    ScanArtifactsPayload,
    SearchArtifactsPayload,
)
from ai.backend.common.dto.manager.v2.artifact_registry.types import ArtifactRegistryType


def _make_revision_data_node(
    status: str = "AVAILABLE",
) -> ArtifactRevisionDataNode:
    now = datetime.now(tz=UTC)
    return ArtifactRevisionDataNode(
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


def _make_artifact_revision_node() -> ArtifactRevisionNode:
    now = datetime.now(tz=UTC)
    return ArtifactRevisionNode(
        id=uuid.uuid4(),
        artifact_id=uuid.uuid4(),
        version="v1.0",
        status=ArtifactStatus.AVAILABLE,
        created_at=now,
        updated_at=now,
    )


class TestArtifactRevisionDataNode:
    """Tests for ArtifactRevisionDataNode model."""

    def test_basic_creation(self) -> None:
        node = _make_revision_data_node()
        assert node.version == "v1.0"
        assert node.status == "AVAILABLE"

    def test_optional_fields_default_to_none(self) -> None:
        node = _make_revision_data_node()
        assert node.readme is None
        assert node.size is None
        assert node.remote_status is None
        assert node.digest is None
        assert node.verification_result is None

    def test_with_readme(self) -> None:
        now = datetime.now(tz=UTC)
        node = ArtifactRevisionDataNode(
            id=uuid.uuid4(),
            artifact_id=uuid.uuid4(),
            version="v2.0",
            readme="# Model README",
            status="PULLED",
            created_at=now,
            updated_at=now,
        )
        assert node.readme == "# Model README"

    def test_serialization_round_trip(self) -> None:
        node = _make_revision_data_node()
        json_str = node.model_dump_json()
        restored = ArtifactRevisionDataNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.version == node.version
        assert restored.status == node.status

    def test_json_contains_expected_fields(self) -> None:
        node = _make_revision_data_node(status="SCANNED")
        parsed = json.loads(node.model_dump_json())
        assert parsed["status"] == "SCANNED"
        assert parsed["version"] == "v1.0"
        assert parsed["readme"] is None


class TestArtifactWithRevisionsNode:
    """Tests for ArtifactWithRevisionsNode model."""

    def _make_node(self) -> ArtifactWithRevisionsNode:
        now = datetime.now(tz=UTC)
        return ArtifactWithRevisionsNode(
            id=uuid.uuid4(),
            name="test-artifact",
            type="MODEL",
            registry_id=uuid.uuid4(),
            source_registry_id=uuid.uuid4(),
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            availability="ALIVE",
            scanned_at=now,
            updated_at=now,
            readonly=False,
        )

    def test_basic_creation(self) -> None:
        node = self._make_node()
        assert node.name == "test-artifact"
        assert node.type == "MODEL"
        assert node.readonly is False

    def test_revisions_default_empty(self) -> None:
        node = self._make_node()
        assert node.revisions == []

    def test_with_revisions(self) -> None:
        rev = _make_revision_data_node()
        node = self._make_node()
        node_with_revs = node.model_copy(update={"revisions": [rev]})
        assert len(node_with_revs.revisions) == 1
        assert node_with_revs.revisions[0].version == "v1.0"

    def test_optional_fields_default_to_none(self) -> None:
        node = self._make_node()
        assert node.description is None
        assert node.extra is None

    def test_serialization_round_trip(self) -> None:
        rev = _make_revision_data_node()
        node = self._make_node()
        node_with_revs = node.model_copy(update={"revisions": [rev]})
        json_str = node_with_revs.model_dump_json()
        restored = ArtifactWithRevisionsNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert len(restored.revisions) == 1


class TestScanArtifactsPayload:
    """Tests for ScanArtifactsPayload model."""

    def test_creation_with_artifacts(self) -> None:
        node = _make_artifact_node()
        payload = ScanArtifactsPayload(artifacts=[node])
        assert len(payload.artifacts) == 1

    def test_empty_artifacts_list(self) -> None:
        payload = ScanArtifactsPayload(artifacts=[])
        assert payload.artifacts == []

    def test_round_trip_serialization(self) -> None:
        node = _make_artifact_node()
        payload = ScanArtifactsPayload(artifacts=[node])
        json_str = payload.model_dump_json()
        restored = ScanArtifactsPayload.model_validate_json(json_str)
        assert len(restored.artifacts) == 1
        assert restored.artifacts[0].id == node.id


class TestDelegateScanArtifactsPayload:
    """Tests for DelegateScanArtifactsPayload model."""

    def test_basic_creation(self) -> None:
        node = _make_artifact_node()
        src_registry_id = uuid.uuid4()
        payload = DelegateScanArtifactsPayload(
            artifacts=[node],
            source_registry_id=src_registry_id,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
        )
        assert len(payload.artifacts) == 1
        assert payload.source_registry_id == src_registry_id
        assert payload.source_registry_type == ArtifactRegistryType.HUGGINGFACE

    def test_readme_data_default_empty(self) -> None:
        node = _make_artifact_node()
        payload = DelegateScanArtifactsPayload(
            artifacts=[node],
            source_registry_id=uuid.uuid4(),
            source_registry_type=ArtifactRegistryType.RESERVOIR,
        )
        assert payload.readme_data == {}

    def test_json_contains_registry_type_string(self) -> None:
        node = _make_artifact_node()
        payload = DelegateScanArtifactsPayload(
            artifacts=[node],
            source_registry_id=uuid.uuid4(),
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
        )
        parsed = json.loads(payload.model_dump_json())
        assert parsed["source_registry_type"] == "huggingface"


class TestDelegateImportArtifactsPayload:
    """Tests for DelegateImportArtifactsPayload model."""

    def test_creation_with_tasks(self) -> None:
        rev_node = _make_artifact_revision_node()
        task_info = ArtifactRevisionImportTaskInfo(
            task_id="task-abc",
            artifact_revision=rev_node,
        )
        payload = DelegateImportArtifactsPayload(tasks=[task_info])
        assert len(payload.tasks) == 1
        assert payload.tasks[0].task_id == "task-abc"

    def test_empty_tasks_list(self) -> None:
        payload = DelegateImportArtifactsPayload(tasks=[])
        assert payload.tasks == []

    def test_round_trip_serialization(self) -> None:
        rev_node = _make_artifact_revision_node()
        task_info = ArtifactRevisionImportTaskInfo(task_id="t1", artifact_revision=rev_node)
        payload = DelegateImportArtifactsPayload(tasks=[task_info])
        json_str = payload.model_dump_json()
        restored = DelegateImportArtifactsPayload.model_validate_json(json_str)
        assert len(restored.tasks) == 1
        assert restored.tasks[0].task_id == "t1"


class TestSearchArtifactsPayload:
    """Tests for SearchArtifactsPayload model."""

    def test_creation_with_artifacts(self) -> None:
        node = _make_artifact_node()
        payload = SearchArtifactsPayload(artifacts=[node])
        assert len(payload.artifacts) == 1

    def test_empty_artifacts(self) -> None:
        payload = SearchArtifactsPayload(artifacts=[])
        assert payload.artifacts == []

    def test_round_trip_serialization(self) -> None:
        node = _make_artifact_node()
        payload = SearchArtifactsPayload(artifacts=[node])
        json_str = payload.model_dump_json()
        restored = SearchArtifactsPayload.model_validate_json(json_str)
        assert len(restored.artifacts) == 1
        assert restored.artifacts[0].name == node.name


class TestScanArtifactModelsPayload:
    """Tests for ScanArtifactModelsPayload model."""

    def test_creation_with_artifact_revision(self) -> None:
        node = _make_artifact_revision_node()
        payload = ScanArtifactModelsPayload(artifact_revision=[node])
        assert len(payload.artifact_revision) == 1

    def test_round_trip_serialization(self) -> None:
        node = _make_artifact_revision_node()
        payload = ScanArtifactModelsPayload(artifact_revision=[node])
        json_str = payload.model_dump_json()
        restored = ScanArtifactModelsPayload.model_validate_json(json_str)
        assert len(restored.artifact_revision) == 1
        assert restored.artifact_revision[0].id == node.id


class TestRetrieveArtifactModelPayload:
    """Tests for RetrieveArtifactModelPayload model."""

    def _make_artifact_with_revisions(self) -> ArtifactWithRevisionsNode:
        now = datetime.now(tz=UTC)
        return ArtifactWithRevisionsNode(
            id=uuid.uuid4(),
            name="gpt2",
            type="MODEL",
            registry_id=uuid.uuid4(),
            source_registry_id=uuid.uuid4(),
            registry_type=ArtifactRegistryType.HUGGINGFACE,
            source_registry_type=ArtifactRegistryType.HUGGINGFACE,
            availability="ALIVE",
            scanned_at=now,
            updated_at=now,
            readonly=False,
        )

    def test_creation(self) -> None:
        artifact = self._make_artifact_with_revisions()
        payload = RetrieveArtifactModelPayload(artifact=artifact)
        assert payload.artifact.name == "gpt2"

    def test_revisions_preserved(self) -> None:
        artifact = self._make_artifact_with_revisions()
        rev = _make_revision_data_node()
        artifact_with_revs = artifact.model_copy(update={"revisions": [rev]})
        payload = RetrieveArtifactModelPayload(artifact=artifact_with_revs)
        assert len(payload.artifact.revisions) == 1

    def test_round_trip_serialization(self) -> None:
        artifact = self._make_artifact_with_revisions()
        payload = RetrieveArtifactModelPayload(artifact=artifact)
        json_str = payload.model_dump_json()
        restored = RetrieveArtifactModelPayload.model_validate_json(json_str)
        assert restored.artifact.id == artifact.id
        assert restored.artifact.name == artifact.name
