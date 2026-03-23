"""Tests for ai.backend.common.dto.manager.v2.domain.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.domain.types import (
    DomainOrderField,
    OrderDirection,
)


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


class TestDomainOrderField:
    """Tests for DomainOrderField enum."""

    def test_name_value(self) -> None:
        assert DomainOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert DomainOrderField.CREATED_AT.value == "created_at"

    def test_modified_at_value(self) -> None:
        assert DomainOrderField.MODIFIED_AT.value == "modified_at"

    def test_enum_members_count(self) -> None:
        assert len(list(DomainOrderField)) == 7

    def test_all_values_are_strings(self) -> None:
        for member in DomainOrderField:
            assert isinstance(member.value, str)

    def test_from_string_name(self) -> None:
        assert DomainOrderField("name") is DomainOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert DomainOrderField("created_at") is DomainOrderField.CREATED_AT

    def test_from_string_modified_at(self) -> None:
        assert DomainOrderField("modified_at") is DomainOrderField.MODIFIED_AT
