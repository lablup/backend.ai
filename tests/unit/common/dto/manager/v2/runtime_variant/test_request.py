"""Unit tests for runtime_variant request DTO validation."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.runtime_variant.request import UpdateRuntimeVariantInput
from ai.backend.common.tristate.unset import UNSET, Unset


class TestUpdateRuntimeVariantInput:
    def test_omitted_fields_are_unset(self) -> None:
        inp = UpdateRuntimeVariantInput(id=uuid4())
        assert isinstance(inp.name, Unset)
        assert isinstance(inp.description, Unset)

    def test_omitted_fields_are_unset_from_dict(self) -> None:
        inp = UpdateRuntimeVariantInput.model_validate({"id": str(uuid4())})
        assert inp.name is UNSET
        assert inp.description is UNSET

    def test_explicit_null_stays_none(self) -> None:
        inp = UpdateRuntimeVariantInput.model_validate({
            "id": str(uuid4()),
            "name": None,
            "description": None,
        })
        assert inp.name is None
        assert inp.description is None

    def test_provided_values_are_kept(self) -> None:
        inp = UpdateRuntimeVariantInput(id=uuid4(), name="vllm", description="desc")
        assert inp.name == "vllm"
        assert inp.description == "desc"

    def test_blank_name_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdateRuntimeVariantInput(id=uuid4(), name="")

    def test_too_long_name_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdateRuntimeVariantInput(id=uuid4(), name="x" * 129)
