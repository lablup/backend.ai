"""Tests for ai.backend.common.dto.manager.v2.login_client_type.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.login_client_type.request import (
    UpdateLoginClientTypeInput,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.tristate.unset import UNSET


class TestUpdateLoginClientTypeInput:
    def test_default_name_is_unset(self) -> None:
        inp = UpdateLoginClientTypeInput()
        assert inp.name is UNSET

    def test_default_description_is_unset(self) -> None:
        inp = UpdateLoginClientTypeInput()
        assert inp.description is UNSET

    def test_name_update(self) -> None:
        inp = UpdateLoginClientTypeInput(name="webui")
        assert inp.name == "webui"

    def test_name_none_stays_none(self) -> None:
        inp = UpdateLoginClientTypeInput(name=None)
        assert inp.name is None

    def test_name_empty_rejected(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateLoginClientTypeInput(name="")

    def test_name_too_long_rejected(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateLoginClientTypeInput(name="a" * 65)

    def test_description_update(self) -> None:
        inp = UpdateLoginClientTypeInput(description="New desc")
        assert inp.description == "New desc"

    def test_description_none_stays_none(self) -> None:
        inp = UpdateLoginClientTypeInput(description=None)
        assert inp.description is None

    def test_omitted_fields_from_json_are_unset(self) -> None:
        inp = UpdateLoginClientTypeInput.model_validate({"name": "core"})
        assert inp.name == "core"
        assert inp.description is UNSET
