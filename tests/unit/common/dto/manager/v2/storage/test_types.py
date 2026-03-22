"""Tests for ai.backend.common.dto.manager.v2.storage.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.storage.types import (
    OrderDirection,
    StorageOrderField,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestStorageOrderField:
    """Tests for StorageOrderField enum."""

    def test_name_value(self) -> None:
        assert StorageOrderField.NAME.value == "name"

    def test_host_value(self) -> None:
        assert StorageOrderField.HOST.value == "host"

    def test_enum_members_count(self) -> None:
        assert len(list(StorageOrderField)) == 2

    def test_from_string_name(self) -> None:
        assert StorageOrderField("name") is StorageOrderField.NAME

    def test_from_string_host(self) -> None:
        assert StorageOrderField("host") is StorageOrderField.HOST
