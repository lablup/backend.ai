"""Tests for ai.backend.common.dto.manager.v2.config.types module."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from ai.backend.common.dto.manager.config.types import (
    MAXIMUM_DOTFILE_SIZE as OriginalMAXIMUM_DOTFILE_SIZE,
)
from ai.backend.common.dto.manager.config.types import (
    DotfilePermission as OriginalDotfilePermission,
)
from ai.backend.common.dto.manager.v2.config.types import (
    MAXIMUM_DOTFILE_SIZE,
    DotfileOrderField,
    DotfilePermission,
    DotfileScope,
    OrderDirection,
)


class _PermissionModel(BaseModel):
    """Helper model for testing DotfilePermission annotation."""

    perm: DotfilePermission


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestDotfileScope:
    """Tests for DotfileScope enum."""

    def test_user_value(self) -> None:
        assert DotfileScope.USER.value == "user"

    def test_group_value(self) -> None:
        assert DotfileScope.GROUP.value == "group"

    def test_domain_value(self) -> None:
        assert DotfileScope.DOMAIN.value == "domain"

    def test_enum_members_count(self) -> None:
        members = list(DotfileScope)
        assert len(members) == 3

    def test_all_values_are_strings(self) -> None:
        for member in DotfileScope:
            assert isinstance(member.value, str)

    def test_from_string_user(self) -> None:
        assert DotfileScope("user") is DotfileScope.USER

    def test_from_string_group(self) -> None:
        assert DotfileScope("group") is DotfileScope.GROUP

    def test_from_string_domain(self) -> None:
        assert DotfileScope("domain") is DotfileScope.DOMAIN


class TestDotfileOrderField:
    """Tests for DotfileOrderField enum."""

    def test_name_value(self) -> None:
        assert DotfileOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert DotfileOrderField.CREATED_AT.value == "created_at"

    def test_enum_members_count(self) -> None:
        members = list(DotfileOrderField)
        assert len(members) == 2

    def test_all_values_are_strings(self) -> None:
        for member in DotfileOrderField:
            assert isinstance(member.value, str)

    def test_from_string_name(self) -> None:
        assert DotfileOrderField("name") is DotfileOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert DotfileOrderField("created_at") is DotfileOrderField.CREATED_AT


class TestReExportedTypes:
    """Tests verifying that types are properly re-exported from the v2 config types module."""

    def test_maximum_dotfile_size_matches_original(self) -> None:
        assert OriginalMAXIMUM_DOTFILE_SIZE == MAXIMUM_DOTFILE_SIZE

    def test_maximum_dotfile_size_value(self) -> None:
        assert MAXIMUM_DOTFILE_SIZE == 64 * 1024

    def test_dotfile_permission_is_same_object(self) -> None:
        assert DotfilePermission is OriginalDotfilePermission


class TestDotfilePermissionValidation:
    """Tests for DotfilePermission annotated type validation."""

    def test_valid_permission_755(self) -> None:
        m = _PermissionModel(perm="755")
        assert m.perm == "755"

    def test_valid_permission_644(self) -> None:
        m = _PermissionModel(perm="644")
        assert m.perm == "644"

    def test_valid_permission_777(self) -> None:
        m = _PermissionModel(perm="777")
        assert m.perm == "777"

    def test_valid_permission_000(self) -> None:
        m = _PermissionModel(perm="000")
        assert m.perm == "000"

    def test_invalid_permission_with_9_rejects(self) -> None:
        with pytest.raises(ValidationError):
            _PermissionModel(perm="999")

    def test_invalid_permission_with_8_rejects(self) -> None:
        with pytest.raises(ValidationError):
            _PermissionModel(perm="888")

    def test_invalid_permission_alpha_rejects(self) -> None:
        with pytest.raises(ValidationError):
            _PermissionModel(perm="abc")

    def test_invalid_permission_too_short_rejects(self) -> None:
        with pytest.raises(ValidationError):
            _PermissionModel(perm="77")

    def test_invalid_permission_too_long_rejects(self) -> None:
        with pytest.raises(ValidationError):
            _PermissionModel(perm="7777")

    def test_invalid_permission_empty_rejects(self) -> None:
        with pytest.raises(ValidationError):
            _PermissionModel(perm="")
