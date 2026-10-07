from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.permission.types import role_scope_types
from ai.backend.common.dto.manager.v2.role_preset.request import CreateRolePresetInput


class TestCreateRolePresetInput:
    @pytest.mark.parametrize("scope_type", role_scope_types(), ids=str)
    def test_accepts_a_role_scope(self, scope_type: EntityType) -> None:
        created = CreateRolePresetInput(name="member", scope_type=scope_type)

        assert created.scope_type == scope_type

    def test_rejects_the_global_scope(self) -> None:
        with pytest.raises(ValidationError):
            CreateRolePresetInput(name="member", scope_type=GlobalEntityType())
