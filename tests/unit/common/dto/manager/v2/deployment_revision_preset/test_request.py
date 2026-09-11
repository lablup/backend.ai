"""Tests for ai.backend.common.dto.manager.v2.deployment_revision_preset.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    UpdateDeploymentRevisionPresetInput,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.tristate.unset import UNSET

_OPTIONAL_FIELDS = (
    "runtime_variant_id",
    "name",
    "rank",
    "resource_slots",
    "resource_opts",
    "cluster_mode",
    "cluster_size",
    "environ",
    "preset_values",
)


class TestUpdateDeploymentRevisionPresetInput:
    @pytest.mark.parametrize("field", _OPTIONAL_FIELDS)
    def test_omitted_field_is_unset(self, field: str) -> None:
        inp = UpdateDeploymentRevisionPresetInput(id=uuid.uuid4())
        assert getattr(inp, field) is UNSET

    @pytest.mark.parametrize("field", _OPTIONAL_FIELDS)
    def test_explicit_none_stays_none(self, field: str) -> None:
        inp = UpdateDeploymentRevisionPresetInput.model_validate({
            "id": str(uuid.uuid4()),
            field: None,
        })
        assert getattr(inp, field) is None

    def test_value_is_kept(self) -> None:
        inp = UpdateDeploymentRevisionPresetInput(id=uuid.uuid4(), name="preset", rank=3)
        assert inp.name == "preset"
        assert inp.rank == 3

    def test_constraints_still_apply(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateDeploymentRevisionPresetInput(id=uuid.uuid4(), name="")
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateDeploymentRevisionPresetInput(id=uuid.uuid4(), cluster_size=0)
