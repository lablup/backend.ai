"""Tests for ai.backend.common.dto.manager.v2.model_card.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.model_card.request import UpdateModelCardInput
from ai.backend.common.tristate.unset import UNSET


class TestUpdateModelCardInput:
    def test_omitted_fields_are_unset(self) -> None:
        inp = UpdateModelCardInput(id=uuid.uuid4())
        assert inp.name is UNSET
        assert inp.author is UNSET
        assert inp.framework is UNSET
        assert inp.label is UNSET
        assert inp.access_level is UNSET

    def test_explicit_none_stays_none(self) -> None:
        inp = UpdateModelCardInput(id=uuid.uuid4(), name=None, framework=None, label=None)
        assert inp.name is None
        assert inp.framework is None
        assert inp.label is None

    def test_values_are_kept(self) -> None:
        inp = UpdateModelCardInput(
            id=uuid.uuid4(), name="card", framework=["pytorch"], label=["nlp"]
        )
        assert inp.name == "card"
        assert inp.framework == ["pytorch"]
        assert inp.label == ["nlp"]

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdateModelCardInput(id=uuid.uuid4(), name="")
