from __future__ import annotations

from typing import Any

import pytest
from aiohttp import web
from pydantic import BaseModel, ValidationError

from ai.backend.common.exception import BackendAIModel, InvalidAPIParameters


class _PayloadTestModel(BackendAIModel):
    """Minimal :class:`BackendAIModel` subclass used to drive the
    override tests without coupling them to a real migrated model's
    schema."""

    name: str
    count: int


class _PlainTestModel(BaseModel):
    """Plain Pydantic model (no ``BackendAIModel`` mixin) used to
    confirm the override is opt-in and stock ``BaseModel`` users still
    get raw ``ValidationError``."""

    name: str


class TestBackendAIModelOverride:
    """Verify that subclasses get automatic ``InvalidAPIParameters``
    (HTTP 400) conversion on validation failure just by inheriting
    :class:`BackendAIModel` — no per-call-site ``try / except`` and no
    sibling ``bai_validate`` method."""

    def test_model_validate_passes_through_on_success(self) -> None:
        """A valid payload returns the model instance unchanged — the
        override must not interfere with the success case."""
        instance = _PayloadTestModel.model_validate({"name": "ok", "count": 1})
        assert isinstance(instance, _PayloadTestModel)
        assert instance.name == "ok"
        assert instance.count == 1

    def test_model_validate_raises_invalid_api_parameters(self) -> None:
        """An invalid payload to ``model_validate`` raises
        :class:`InvalidAPIParameters` (HTTP 400) carrying the
        structured per-field error list."""
        with pytest.raises(InvalidAPIParameters) as excinfo:
            _PayloadTestModel.model_validate({"count": "not-a-number"})

        err = excinfo.value
        assert isinstance(err, web.HTTPBadRequest)
        assert err.status_code == 400
        assert err.extra_msg is not None
        assert err.extra_data is not None
        locs = {e["loc"] for e in err.extra_data["errors"]}
        assert "name" in locs
        assert "count" in locs

    def test_model_validate_json_is_also_overridden(self) -> None:
        """The JSON variant must follow the same contract so callers
        decoding raw request bodies aren't an exception to the rule."""
        with pytest.raises(InvalidAPIParameters):
            _PayloadTestModel.model_validate_json('{"count": "nope"}')

    def test_constructor_keeps_stock_pydantic_error(self) -> None:
        """``__init__`` is intentionally NOT overridden so internal
        default-value construction (``Model(field=...)``) keeps stock
        Pydantic semantics — only the validate entry points convert.
        ``Any``-typed kwargs are used here so the deliberately wrong
        ``count`` value isn't second-guessed at type-check time."""
        bad_kwargs: Any = {"name": "ok", "count": "not-a-number"}
        with pytest.raises(ValidationError):
            _PayloadTestModel(**bad_kwargs)

    def test_plain_basemodel_still_raises_validation_error(self) -> None:
        """Without inheriting :class:`BackendAIModel` a model keeps
        the standard Pydantic behavior — the override is fully
        opt-in."""
        with pytest.raises(ValidationError):
            _PlainTestModel.model_validate({})
