"""Tests for ai.backend.common.dto.manager.v2.object_storage.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.object_storage.types import (
    ObjectStorageOrderField,
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

    def test_from_string(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC
        assert OrderDirection("DESC") is OrderDirection.DESC


class TestObjectStorageOrderField:
    """Tests for ObjectStorageOrderField enum."""

    def test_name_value(self) -> None:
        assert ObjectStorageOrderField.NAME.value == "name"

    def test_host_value(self) -> None:
        assert ObjectStorageOrderField.HOST.value == "host"

    def test_region_value(self) -> None:
        assert ObjectStorageOrderField.REGION.value == "region"

    def test_created_at_value(self) -> None:
        assert ObjectStorageOrderField.CREATED_AT.value == "created_at"

    def test_enum_members_count(self) -> None:
        assert len(list(ObjectStorageOrderField)) == 4

    def test_from_string_name(self) -> None:
        assert ObjectStorageOrderField("name") is ObjectStorageOrderField.NAME

    def test_from_string_host(self) -> None:
        assert ObjectStorageOrderField("host") is ObjectStorageOrderField.HOST
