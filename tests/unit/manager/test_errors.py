from __future__ import annotations

import pytest
from aiohttp import web
from pydantic import ValidationError

from ai.backend.common.exception import ApiPayloadModel, InvalidAPIParameters


class _BaiTestModel(ApiPayloadModel):
    """Minimal :class:`ApiPayloadModel` subclass used to drive the
    ``bai_validate`` tests without coupling them to a real migrated
    model's schema."""

    name: str
    count: int


class TestApiPayloadModelBaiValidate:
    """Cover the ``ApiPayloadModel.bai_validate`` mechanism — verifies
    that subclasses get automatic ``InvalidAPIParameters`` (HTTP 400)
    conversion on validation failure just by inheriting, removing the
    need for ``try / except ValidationError`` wrappers at every call
    site."""

    def test_bai_validate_passes_through_on_success(self) -> None:
        """A valid payload returns the model instance unchanged — the
        ``bai_validate`` path must not interfere with the success
        case."""
        instance = _BaiTestModel.bai_validate({"name": "ok", "count": 1})
        assert isinstance(instance, _BaiTestModel)
        assert instance.name == "ok"
        assert instance.count == 1

    def test_bai_validate_raises_invalid_api_parameters(self) -> None:
        """An invalid payload raises :class:`InvalidAPIParameters` (an
        HTTP 400) carrying the structured field-error list — that is
        what the whole abstraction exists for."""
        with pytest.raises(InvalidAPIParameters) as excinfo:
            _BaiTestModel.bai_validate({"count": "not-a-number"})

        err = excinfo.value
        assert isinstance(err, web.HTTPBadRequest)
        assert err.status_code == 400
        assert err.extra_msg is not None
        assert err.extra_data is not None
        locs = {e["loc"] for e in err.extra_data["errors"]}
        assert "name" in locs
        assert "count" in locs

    def test_model_validate_still_raises_pydantic_error(self) -> None:
        """Plain ``model_validate`` keeps stock Pydantic semantics so
        the same model can be reused in non-HTTP contexts (bootstrap,
        DB row deserialization) without surfacing HTTP-shaped errors
        there."""
        with pytest.raises(ValidationError):
            _BaiTestModel.model_validate({"count": "not-a-number"})
