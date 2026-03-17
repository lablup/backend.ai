"""Tests for ai.backend.common.dto.manager.v2.quota_scope.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.quota_scope.types import (
    OrderDirection,
    QuotaScopeOrderField,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_from_string(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC
        assert OrderDirection("desc") is OrderDirection.DESC


class TestQuotaScopeOrderField:
    """Tests for QuotaScopeOrderField enum."""

    def test_quota_scope_id_value(self) -> None:
        assert QuotaScopeOrderField.QUOTA_SCOPE_ID.value == "quota_scope_id"

    def test_storage_host_name_value(self) -> None:
        assert QuotaScopeOrderField.STORAGE_HOST_NAME.value == "storage_host_name"

    def test_enum_members_count(self) -> None:
        assert len(list(QuotaScopeOrderField)) == 2

    def test_from_string_quota_scope_id(self) -> None:
        assert QuotaScopeOrderField("quota_scope_id") is QuotaScopeOrderField.QUOTA_SCOPE_ID

    def test_from_string_storage_host_name(self) -> None:
        assert QuotaScopeOrderField("storage_host_name") is QuotaScopeOrderField.STORAGE_HOST_NAME
