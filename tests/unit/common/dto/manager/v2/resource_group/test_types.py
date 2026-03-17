"""Tests for ai.backend.common.dto.manager.v2.resource_group.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.resource_group.types import (
    OrderDirection,
    ResourceGroupOrderField,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_all_values_present(self) -> None:
        values = {e.value for e in OrderDirection}
        assert values == {"asc", "desc"}


class TestResourceGroupOrderField:
    """Tests for ResourceGroupOrderField enum."""

    def test_name_value(self) -> None:
        assert ResourceGroupOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert ResourceGroupOrderField.CREATED_AT.value == "created_at"

    def test_modified_at_value(self) -> None:
        assert ResourceGroupOrderField.MODIFIED_AT.value == "modified_at"

    def test_all_values_present(self) -> None:
        values = {e.value for e in ResourceGroupOrderField}
        assert values == {"name", "created_at", "modified_at"}
