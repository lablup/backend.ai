"""Tests for ai.backend.common.dto.manager.v2.group.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.group.types import (
    GroupOrderField,
    OrderDirection,
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
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestGroupOrderField:
    """Tests for GroupOrderField enum."""

    def test_name_value(self) -> None:
        assert GroupOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert GroupOrderField.CREATED_AT.value == "created_at"

    def test_modified_at_value(self) -> None:
        assert GroupOrderField.MODIFIED_AT.value == "modified_at"

    def test_enum_members_count(self) -> None:
        assert len(list(GroupOrderField)) == 8

    def test_all_values_are_strings(self) -> None:
        for member in GroupOrderField:
            assert isinstance(member.value, str)

    def test_from_string_name(self) -> None:
        assert GroupOrderField("name") is GroupOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert GroupOrderField("created_at") is GroupOrderField.CREATED_AT

    def test_from_string_modified_at(self) -> None:
        assert GroupOrderField("modified_at") is GroupOrderField.MODIFIED_AT
