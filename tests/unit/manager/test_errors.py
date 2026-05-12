from __future__ import annotations

from typing import Any

import pytest
from aiohttp import web
from pydantic import ValidationError

from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.types import BackendAISchema


class _PayloadTestModel(BackendAISchema):
    name: str
    count: int


class TestBackendAISchemaOverride:
    """``BackendAISchema`` subclasses get the auto-conversion override
    just by inheriting — no per-call-site ``try / except``."""

    def test_model_validate_passes_through_on_success(self) -> None:
        instance = _PayloadTestModel.model_validate({"name": "ok", "count": 1})
        assert isinstance(instance, _PayloadTestModel)
        assert instance.name == "ok"
        assert instance.count == 1

    def test_model_validate_raises_model_validation_failed(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed) as excinfo:
            _PayloadTestModel.model_validate({"count": "not-a-number"})

        err = excinfo.value
        assert isinstance(err, web.HTTPBadRequest)
        assert err.status_code == 400
        assert err.extra_msg is not None
        locs = {entry["loc"] for entry in err.errors()}
        assert ("name",) in locs
        assert ("count",) in locs

    def test_model_validate_json_is_also_overridden(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            _PayloadTestModel.model_validate_json('{"count": "nope"}')

    def test_constructor_keeps_stock_pydantic_error(self) -> None:
        """``__init__`` is intentionally NOT overridden (see
        ``BackendAISchema`` docstring): direct ``Model(field=...)``
        construction still raises stock ``pydantic.ValidationError``."""
        bad_kwargs: Any = {"name": "ok", "count": "not-a-number"}
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            _PayloadTestModel(**bad_kwargs)
