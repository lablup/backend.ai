"""Tests for ai.backend.common.dto.manager.v2.group.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.group.types import (
    OrderDirection,
    ProjectOrderField,
    ProjectType,
)


class TestProjectType:
    """Tests for ProjectType enum."""

    def test_general_value(self) -> None:
        assert ProjectType.GENERAL.value == "general"

    def test_model_store_value(self) -> None:
        assert ProjectType.MODEL_STORE.value == "model-store"

    def test_enum_members_count(self) -> None:
        assert len(list(ProjectType)) == 2

    def test_all_values_are_strings(self) -> None:
        for member in ProjectType:
            assert isinstance(member.value, str)

    def test_from_string_general(self) -> None:
        assert ProjectType("general") is ProjectType.GENERAL

    def test_from_string_model_store(self) -> None:
        assert ProjectType("model-store") is ProjectType.MODEL_STORE


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_from_string_asc(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("DESC") is OrderDirection.DESC


class TestProjectOrderField:
    """Tests for ProjectOrderField enum."""

    def test_name_value(self) -> None:
        assert ProjectOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert ProjectOrderField.CREATED_AT.value == "created_at"

    def test_modified_at_value(self) -> None:
        assert ProjectOrderField.MODIFIED_AT.value == "modified_at"

    def test_enum_members_count(self) -> None:
        assert len(list(ProjectOrderField)) == 8

    def test_all_values_are_strings(self) -> None:
        for member in ProjectOrderField:
            assert isinstance(member.value, str)

    def test_from_string_name(self) -> None:
        assert ProjectOrderField("name") is ProjectOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert ProjectOrderField("created_at") is ProjectOrderField.CREATED_AT

    def test_from_string_modified_at(self) -> None:
        assert ProjectOrderField("modified_at") is ProjectOrderField.MODIFIED_AT
