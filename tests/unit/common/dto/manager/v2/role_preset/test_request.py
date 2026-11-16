"""Unit tests for role preset request DTO validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.dto.manager.v2.role_preset.request import CreateRolePresetInput


class TestCreateRolePresetInput:
    def test_a_project_preset_takes_owner_assign(self) -> None:
        inp = CreateRolePresetInput(
            name="preset", scope_type=ProjectEntityType(), auto_assign_to_owner=True
        )
        assert inp.auto_assign_to_owner is True

    def test_a_preset_of_another_scope_refuses_owner_assign(self) -> None:
        with pytest.raises(ValidationError):
            CreateRolePresetInput(
                name="preset", scope_type=DomainEntityType(), auto_assign_to_owner=True
            )

    def test_a_preset_of_another_scope_leaves_owner_assign_off(self) -> None:
        inp = CreateRolePresetInput(name="preset", scope_type=DomainEntityType())
        assert inp.auto_assign_to_owner is False
