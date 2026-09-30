"""Tests for the filter conversion of RolePresetAdapter."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from ai.backend.common.dto.manager.query import UUIDFilter
from ai.backend.common.dto.manager.v2.role_preset.request import RolePresetFilter
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter

_PRESET_ID = uuid.uuid4()


@dataclass(frozen=True)
class _IdFilterCase:
    name: str
    id_filter: UUIDFilter
    expected_sql: str


@pytest.fixture
def adapter() -> RolePresetAdapter:
    return RolePresetAdapter(MagicMock())


class TestRolePresetIdFilter:
    @pytest.mark.parametrize(
        "case",
        [
            _IdFilterCase(
                name="equals",
                id_filter=UUIDFilter(equals=_PRESET_ID),
                expected_sql="role_presets.id = :id_1",
            ),
            _IdFilterCase(
                name="not_equals",
                id_filter=UUIDFilter(not_equals=_PRESET_ID),
                expected_sql="role_presets.id != :id_1",
            ),
            _IdFilterCase(
                name="in",
                id_filter=UUIDFilter(in_=[_PRESET_ID]),
                expected_sql="role_presets.id IN (__[POSTCOMPILE_id_1])",
            ),
            _IdFilterCase(
                name="not_in",
                id_filter=UUIDFilter(not_in=[_PRESET_ID]),
                expected_sql="(role_presets.id NOT IN (__[POSTCOMPILE_id_1]))",
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_an_id_filter_narrows_presets_by_their_id(
        self, adapter: RolePresetAdapter, case: _IdFilterCase
    ) -> None:
        conditions = adapter._convert_filter(RolePresetFilter(id=case.id_filter))

        assert [str(condition().compile()) for condition in conditions] == [case.expected_sql]
