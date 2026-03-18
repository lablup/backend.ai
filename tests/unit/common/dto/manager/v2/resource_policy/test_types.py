"""Tests for ai.backend.common.dto.manager.v2.resource_policy.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.resource_policy.types import (
    DefaultForUnspecified,
    KeypairResourcePolicyOrderField,
    OrderDirection,
    ProjectResourcePolicyOrderField,
    UserResourcePolicyOrderField,
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


class TestDefaultForUnspecified:
    """Tests for DefaultForUnspecified re-export."""

    def test_limited_value(self) -> None:
        assert DefaultForUnspecified.LIMITED.value == "LIMITED"

    def test_unlimited_value(self) -> None:
        assert DefaultForUnspecified.UNLIMITED.value == "UNLIMITED"

    def test_all_values_present(self) -> None:
        values = {e.value for e in DefaultForUnspecified}
        assert "LIMITED" in values
        assert "UNLIMITED" in values


class TestKeypairResourcePolicyOrderField:
    """Tests for KeypairResourcePolicyOrderField enum."""

    def test_name_value(self) -> None:
        assert KeypairResourcePolicyOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert KeypairResourcePolicyOrderField.CREATED_AT.value == "created_at"

    def test_all_values_present(self) -> None:
        values = {e.value for e in KeypairResourcePolicyOrderField}
        assert values == {"name", "created_at"}


class TestUserResourcePolicyOrderField:
    """Tests for UserResourcePolicyOrderField enum."""

    def test_name_value(self) -> None:
        assert UserResourcePolicyOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert UserResourcePolicyOrderField.CREATED_AT.value == "created_at"

    def test_all_values_present(self) -> None:
        values = {e.value for e in UserResourcePolicyOrderField}
        assert values == {"name", "created_at"}


class TestProjectResourcePolicyOrderField:
    """Tests for ProjectResourcePolicyOrderField enum."""

    def test_name_value(self) -> None:
        assert ProjectResourcePolicyOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert ProjectResourcePolicyOrderField.CREATED_AT.value == "created_at"

    def test_all_values_present(self) -> None:
        values = {e.value for e in ProjectResourcePolicyOrderField}
        assert values == {"name", "created_at"}
