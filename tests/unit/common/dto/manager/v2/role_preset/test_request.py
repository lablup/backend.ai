from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.dto.manager.v2.role_preset.request import CreateRolePresetInput


class TestCreateRolePresetInput:
    def test_rejects_the_global_scope(self) -> None:
        with pytest.raises(ValidationError):
            CreateRolePresetInput(name="member", scope_type=GlobalEntityType())
