"""Tests for ai.backend.common.dto.manager.v2.artifact_registry.types module."""

from __future__ import annotations

import json

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.dto.manager.v2.artifact_registry.types import (
    ArtifactOrderingField,
    ArtifactRevisionReadmeInfo,
    OrderDirection,
)
from ai.backend.common.dto.manager.v2.artifact_registry.types import (
    ArtifactRegistryType as ExportedArtifactRegistryType,
)


class TestArtifactOrderingField:
    """Tests for ArtifactOrderingField enum."""

    def test_name_value(self) -> None:
        assert ArtifactOrderingField.NAME.value == "NAME"

    def test_type_value(self) -> None:
        assert ArtifactOrderingField.TYPE.value == "TYPE"

    def test_size_value(self) -> None:
        assert ArtifactOrderingField.SIZE.value == "SIZE"

    def test_scanned_at_value(self) -> None:
        assert ArtifactOrderingField.SCANNED_AT.value == "SCANNED_AT"

    def test_updated_at_value(self) -> None:
        assert ArtifactOrderingField.UPDATED_AT.value == "UPDATED_AT"

    def test_all_values_are_strings(self) -> None:
        for member in ArtifactOrderingField:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(ArtifactOrderingField)
        assert len(members) == 5

    def test_from_string_name(self) -> None:
        assert ArtifactOrderingField("NAME") is ArtifactOrderingField.NAME

    def test_from_string_type(self) -> None:
        assert ArtifactOrderingField("TYPE") is ArtifactOrderingField.TYPE


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestReExportedArtifactRegistryType:
    """Tests verifying ArtifactRegistryType is properly re-exported."""

    def test_is_same_object(self) -> None:
        assert ExportedArtifactRegistryType is ArtifactRegistryType

    def test_huggingface_value(self) -> None:
        assert ExportedArtifactRegistryType.HUGGINGFACE.value == "huggingface"

    def test_reservoir_value(self) -> None:
        assert ExportedArtifactRegistryType.RESERVOIR.value == "reservoir"

    def test_from_string_huggingface(self) -> None:
        assert ExportedArtifactRegistryType("huggingface") is ArtifactRegistryType.HUGGINGFACE


class TestArtifactRevisionReadmeInfo:
    """Tests for ArtifactRevisionReadmeInfo sub-model."""

    def test_readme_defaults_to_none(self) -> None:
        info = ArtifactRevisionReadmeInfo()
        assert info.readme is None

    def test_creation_with_readme(self) -> None:
        info = ArtifactRevisionReadmeInfo(readme="# My Model")
        assert info.readme == "# My Model"

    def test_creation_with_none_readme(self) -> None:
        info = ArtifactRevisionReadmeInfo(readme=None)
        assert info.readme is None

    def test_serialization_round_trip(self) -> None:
        info = ArtifactRevisionReadmeInfo(readme="# README content")
        json_str = info.model_dump_json()
        restored = ArtifactRevisionReadmeInfo.model_validate_json(json_str)
        assert restored.readme == "# README content"

    def test_model_dump_json_with_none(self) -> None:
        info = ArtifactRevisionReadmeInfo()
        parsed = json.loads(info.model_dump_json())
        assert parsed["readme"] is None

    def test_model_dump_json_with_content(self) -> None:
        info = ArtifactRevisionReadmeInfo(readme="# Hello")
        parsed = json.loads(info.model_dump_json())
        assert parsed["readme"] == "# Hello"

    def test_model_validate_from_dict(self) -> None:
        info = ArtifactRevisionReadmeInfo.model_validate({"readme": "# Test"})
        assert info.readme == "# Test"
