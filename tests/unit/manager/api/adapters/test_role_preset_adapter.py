"""Tests for the role preset adapter's DTO-filter conversion."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.common.dto.manager.v2.role_preset.request import RolePresetFilter
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter


def _make_adapter() -> RolePresetAdapter:
    return RolePresetAdapter(MagicMock())


class TestRolePresetAdapterConvertFilter:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (True, "role_presets.auto_assign_to_owner = true"),
            (False, "role_presets.auto_assign_to_owner = false"),
        ],
        ids=["flagged", "unflagged"],
    )
    def test_auto_assign_to_owner_matches_its_own_column(self, value: bool, expected: str) -> None:
        filter_dto = RolePresetFilter(auto_assign_to_owner=value)

        conditions = _make_adapter()._convert_filter(filter_dto)

        assert [str(condition().compile()) for condition in conditions] == [expected]

    def test_omitted_auto_assign_to_owner_produces_no_condition(self) -> None:
        assert _make_adapter()._convert_filter(RolePresetFilter()) == []
