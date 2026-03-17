"""Tests for ai.backend.common.dto.manager.v2.artifact.types module."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    VerificationStepResult,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactOrderField,
    ArtifactRevisionInfo,
    ArtifactRevisionOrderField,
    ArtifactStatus,
    ArtifactType,
    OrderDirection,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactRegistryType as ExportedArtifactRegistryType,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    VerificationStepResult as ExportedVerificationStepResult,
)


class TestArtifactType:
    """Tests for ArtifactType enum."""

    def test_model_value(self) -> None:
        assert ArtifactType.MODEL.value == "MODEL"

    def test_package_value(self) -> None:
        assert ArtifactType.PACKAGE.value == "PACKAGE"

    def test_image_value(self) -> None:
        assert ArtifactType.IMAGE.value == "IMAGE"

    def test_all_values_are_strings(self) -> None:
        for member in ArtifactType:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(ArtifactType)
        assert len(members) == 3

    def test_from_string_model(self) -> None:
        assert ArtifactType("MODEL") is ArtifactType.MODEL


class TestArtifactStatus:
    """Tests for ArtifactStatus enum."""

    def test_scanned_value(self) -> None:
        assert ArtifactStatus.SCANNED.value == "SCANNED"

    def test_available_value(self) -> None:
        assert ArtifactStatus.AVAILABLE.value == "AVAILABLE"

    def test_failed_value(self) -> None:
        assert ArtifactStatus.FAILED.value == "FAILED"

    def test_all_values_are_strings(self) -> None:
        for member in ArtifactStatus:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(ArtifactStatus)
        assert len(members) == 8

    def test_from_string_available(self) -> None:
        assert ArtifactStatus("AVAILABLE") is ArtifactStatus.AVAILABLE


class TestArtifactAvailability:
    """Tests for ArtifactAvailability enum."""

    def test_alive_value(self) -> None:
        assert ArtifactAvailability.ALIVE.value == "ALIVE"

    def test_deleted_value(self) -> None:
        assert ArtifactAvailability.DELETED.value == "DELETED"

    def test_enum_members_count(self) -> None:
        members = list(ArtifactAvailability)
        assert len(members) == 2


class TestArtifactOrderField:
    """Tests for ArtifactOrderField enum."""

    def test_name_value(self) -> None:
        assert ArtifactOrderField.NAME.value == "NAME"

    def test_type_value(self) -> None:
        assert ArtifactOrderField.TYPE.value == "TYPE"

    def test_size_value(self) -> None:
        assert ArtifactOrderField.SIZE.value == "SIZE"

    def test_scanned_at_value(self) -> None:
        assert ArtifactOrderField.SCANNED_AT.value == "SCANNED_AT"

    def test_updated_at_value(self) -> None:
        assert ArtifactOrderField.UPDATED_AT.value == "UPDATED_AT"

    def test_enum_members_count(self) -> None:
        members = list(ArtifactOrderField)
        assert len(members) == 5


class TestArtifactRevisionOrderField:
    """Tests for ArtifactRevisionOrderField enum."""

    def test_version_value(self) -> None:
        assert ArtifactRevisionOrderField.VERSION.value == "VERSION"

    def test_size_value(self) -> None:
        assert ArtifactRevisionOrderField.SIZE.value == "SIZE"

    def test_created_at_value(self) -> None:
        assert ArtifactRevisionOrderField.CREATED_AT.value == "CREATED_AT"

    def test_updated_at_value(self) -> None:
        assert ArtifactRevisionOrderField.UPDATED_AT.value == "UPDATED_AT"

    def test_status_value(self) -> None:
        assert ArtifactRevisionOrderField.STATUS.value == "STATUS"

    def test_enum_members_count(self) -> None:
        members = list(ArtifactRevisionOrderField)
        assert len(members) == 5


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestReExportedTypes:
    """Tests verifying that types are properly re-exported from types module."""

    def test_artifact_registry_type_is_same_object(self) -> None:
        assert ExportedArtifactRegistryType is ArtifactRegistryType

    def test_verification_step_result_is_same_object(self) -> None:
        assert ExportedVerificationStepResult is VerificationStepResult

    def test_artifact_registry_type_huggingface_value(self) -> None:
        assert ExportedArtifactRegistryType.HUGGINGFACE.value == "huggingface"

    def test_artifact_registry_type_reservoir_value(self) -> None:
        assert ExportedArtifactRegistryType.RESERVOIR.value == "reservoir"


class TestArtifactRevisionInfo:
    """Tests for ArtifactRevisionInfo sub-model creation."""

    def test_basic_creation(self) -> None:
        rev_id = uuid4()
        now = datetime.now(tz=UTC)
        info = ArtifactRevisionInfo(
            id=rev_id,
            version="v1.0",
            status=ArtifactStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
        )
        assert info.id == rev_id
        assert info.version == "v1.0"
        assert info.status == ArtifactStatus.AVAILABLE
        assert info.created_at == now

    def test_size_defaults_to_none(self) -> None:
        rev_id = uuid4()
        now = datetime.now(tz=UTC)
        info = ArtifactRevisionInfo(
            id=rev_id,
            version="v1.0",
            status=ArtifactStatus.SCANNED,
            created_at=now,
            updated_at=now,
        )
        assert info.size is None

    def test_with_size(self) -> None:
        rev_id = uuid4()
        now = datetime.now(tz=UTC)
        info = ArtifactRevisionInfo(
            id=rev_id,
            version="v2.0",
            size=1024,
            status=ArtifactStatus.PULLED,
            created_at=now,
            updated_at=now,
        )
        assert info.size == 1024

    def test_serialization_round_trip(self) -> None:
        rev_id = uuid4()
        now = datetime.now(tz=UTC)
        info = ArtifactRevisionInfo(
            id=rev_id,
            version="v1.0",
            size=512,
            status=ArtifactStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
        )
        json_str = info.model_dump_json()
        restored = ArtifactRevisionInfo.model_validate_json(json_str)
        assert restored.id == rev_id
        assert restored.version == "v1.0"
        assert restored.size == 512
        assert restored.status == ArtifactStatus.AVAILABLE

    def test_model_dump_json_contains_status_string(self) -> None:
        rev_id = uuid4()
        now = datetime.now(tz=UTC)
        info = ArtifactRevisionInfo(
            id=rev_id,
            version="v1.0",
            status=ArtifactStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
        )
        parsed = json.loads(info.model_dump_json())
        assert parsed["status"] == "AVAILABLE"
        assert parsed["version"] == "v1.0"
