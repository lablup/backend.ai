"""Tests for ai.backend.common.dto.manager.v2.artifact.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.artifact.request import (
    CancelImportTaskInput,
    CleanupRevisionsInput,
    ImportArtifactsInput,
    ImportArtifactsOptionsInput,
    UpdateArtifactInput,
)


class TestUpdateArtifactInput:
    """Tests for UpdateArtifactInput model creation and validation."""

    def test_default_description_is_sentinel(self) -> None:
        req = UpdateArtifactInput()
        assert req.description is SENTINEL
        assert isinstance(req.description, Sentinel)

    def test_explicit_sentinel_description_signals_clear(self) -> None:
        req = UpdateArtifactInput(description=SENTINEL)
        assert req.description is SENTINEL

    def test_none_description_means_no_change(self) -> None:
        req = UpdateArtifactInput(description=None)
        assert req.description is None

    def test_string_description_sets_value(self) -> None:
        req = UpdateArtifactInput(description="New description")
        assert req.description == "New description"

    def test_description_whitespace_stripped(self) -> None:
        req = UpdateArtifactInput(description="  trimmed  ")
        assert req.description == "trimmed"

    def test_description_whitespace_only_becomes_none(self) -> None:
        req = UpdateArtifactInput(description="   ")
        assert req.description is None

    def test_readonly_default_is_none(self) -> None:
        req = UpdateArtifactInput()
        assert req.readonly is None

    def test_readonly_true(self) -> None:
        req = UpdateArtifactInput(readonly=True)
        assert req.readonly is True

    def test_readonly_false(self) -> None:
        req = UpdateArtifactInput(readonly=False)
        assert req.readonly is False

    def test_all_none_is_valid(self) -> None:
        req = UpdateArtifactInput(readonly=None, description=None)
        assert req.readonly is None
        assert req.description is None


class TestImportArtifactsInput:
    """Tests for ImportArtifactsInput model creation and validation."""

    def test_basic_creation_with_ids(self) -> None:
        rev_id = uuid.uuid4()
        req = ImportArtifactsInput(artifact_revision_ids=[rev_id])
        assert req.artifact_revision_ids == [rev_id]

    def test_multiple_ids(self) -> None:
        ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        req = ImportArtifactsInput(artifact_revision_ids=ids)
        assert len(req.artifact_revision_ids) == 3

    def test_options_default_is_none(self) -> None:
        rev_id = uuid.uuid4()
        req = ImportArtifactsInput(artifact_revision_ids=[rev_id])
        assert req.options is None

    def test_options_force_default_is_false(self) -> None:
        req = ImportArtifactsOptionsInput()
        assert req.force is False

    def test_options_force_true(self) -> None:
        req = ImportArtifactsOptionsInput(force=True)
        assert req.force is True

    def test_vfolder_id_default_is_none(self) -> None:
        rev_id = uuid.uuid4()
        req = ImportArtifactsInput(artifact_revision_ids=[rev_id])
        assert req.vfolder_id is None

    def test_vfolder_id_set(self) -> None:
        rev_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()
        req = ImportArtifactsInput(artifact_revision_ids=[rev_id], vfolder_id=vfolder_id)
        assert req.vfolder_id == vfolder_id

    def test_missing_artifact_revision_ids_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ImportArtifactsInput.model_validate({})

    def test_round_trip_serialization(self) -> None:
        rev_id = uuid.uuid4()
        req = ImportArtifactsInput(
            artifact_revision_ids=[rev_id],
            options=ImportArtifactsOptionsInput(force=True),
        )
        json_data = req.model_dump_json()
        restored = ImportArtifactsInput.model_validate_json(json_data)
        assert restored.artifact_revision_ids == [rev_id]
        assert restored.options is not None
        assert restored.options.force is True


class TestCleanupRevisionsInput:
    """Tests for CleanupRevisionsInput model creation and validation."""

    def test_basic_creation_with_ids(self) -> None:
        rev_id = uuid.uuid4()
        req = CleanupRevisionsInput(artifact_revision_ids=[rev_id])
        assert req.artifact_revision_ids == [rev_id]

    def test_multiple_ids(self) -> None:
        ids = [uuid.uuid4(), uuid.uuid4()]
        req = CleanupRevisionsInput(artifact_revision_ids=ids)
        assert len(req.artifact_revision_ids) == 2

    def test_empty_list_is_valid(self) -> None:
        req = CleanupRevisionsInput(artifact_revision_ids=[])
        assert req.artifact_revision_ids == []

    def test_missing_ids_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CleanupRevisionsInput.model_validate({})

    def test_round_trip_serialization(self) -> None:
        ids = [uuid.uuid4(), uuid.uuid4()]
        req = CleanupRevisionsInput(artifact_revision_ids=ids)
        json_data = req.model_dump_json()
        restored = CleanupRevisionsInput.model_validate_json(json_data)
        assert restored.artifact_revision_ids == ids


class TestCancelImportTaskInput:
    """Tests for CancelImportTaskInput model creation and validation."""

    def test_basic_creation(self) -> None:
        rev_id = uuid.uuid4()
        req = CancelImportTaskInput(artifact_revision_id=rev_id)
        assert req.artifact_revision_id == rev_id

    def test_id_is_uuid_instance(self) -> None:
        rev_id = uuid.uuid4()
        req = CancelImportTaskInput(artifact_revision_id=rev_id)
        assert isinstance(req.artifact_revision_id, uuid.UUID)

    def test_from_string_uuid(self) -> None:
        rev_id = uuid.uuid4()
        req = CancelImportTaskInput.model_validate({"artifact_revision_id": str(rev_id)})
        assert req.artifact_revision_id == rev_id

    def test_invalid_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CancelImportTaskInput.model_validate({"artifact_revision_id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CancelImportTaskInput.model_validate({})

    def test_round_trip_serialization(self) -> None:
        rev_id = uuid.uuid4()
        req = CancelImportTaskInput(artifact_revision_id=rev_id)
        json_data = req.model_dump_json()
        restored = CancelImportTaskInput.model_validate_json(json_data)
        assert restored.artifact_revision_id == rev_id
