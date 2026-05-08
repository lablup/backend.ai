from __future__ import annotations

import pytest
from aiohttp import web
from pydantic import BaseModel, ValidationError

from ai.backend.common.exception import (
    BackendAIModel,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.kernel import InvalidResourceOpts, InvalidSessionCreationConfig


class _DummyConfig(BaseModel):
    """Stand-in for a real ``CreationConfigVN`` so the test does not
    depend on the full session-creation schema."""

    image: str
    cluster_size: int


class TestInvalidSessionCreationConfig:
    """Pin the wire contract of one representative domain error class
    (used by the V1-V7 ``CreationConfig`` wraps in
    ``api/rest/session/handler.py``). The other ``Invalid*`` classes
    introduced by this PR follow the same shape."""

    def test_status_and_error_code(self) -> None:
        """Bad-payload error must surface as HTTP 400 with the
        ``session_create_invalid-parameters`` error code so callers can
        distinguish "user payload was wrong" from generic 500s."""
        err = InvalidSessionCreationConfig(extra_msg="bad")
        assert isinstance(err, web.HTTPBadRequest)
        assert err.status_code == 400

        code = err.error_code()
        assert code.domain == ErrorDomain.SESSION
        assert code.operation == ErrorOperation.CREATE
        assert code.error_detail == ErrorDetail.INVALID_PARAMETERS

    def test_from_pydantic_carries_structured_field_errors(self) -> None:
        """The shared ``BackendAIError.from_pydantic`` must wrap a
        ``ValidationError`` so the response body still names every
        offending field — that is the whole point of the per-domain
        wrapping introduced by this PR."""
        try:
            _DummyConfig.model_validate({"cluster_size": "not-a-number"})
        except ValidationError as exc:
            err = InvalidSessionCreationConfig.from_pydantic(exc)
        else:
            pytest.fail("Expected ValidationError")

        # Human-readable summary must mention each missing/invalid field.
        assert err.extra_msg is not None
        assert "image" in err.extra_msg
        assert "cluster_size" in err.extra_msg

        # Structured payload preserves every error so clients can render
        # per-field messages without re-parsing the summary string.
        assert err.extra_data is not None
        errors = err.extra_data["errors"]
        locs = {e["loc"] for e in errors}
        assert "image" in locs
        assert "cluster_size" in locs


class _BaiTestModel(BackendAIModel):
    """A minimal subclass that opts into automatic
    :class:`InvalidResourceOpts` conversion. We use it instead of a
    real migrated model so the test isn't coupled to whatever
    ``ResourceOpts`` happens to declare today."""

    __bai_error_class__ = InvalidResourceOpts

    name: str
    count: int


class TestBackendAIModelBaiValidate:
    """Cover the ``BackendAIModel.bai_validate`` mechanism — verifies
    that subclasses opt into automatic ``BackendAIError`` conversion
    just by setting ``__bai_error_class__``, removing the need for
    try/except wrappers at every call site."""

    def test_bai_validate_passes_through_on_success(self) -> None:
        """A valid payload returns the model instance unchanged — the
        ``bai_validate`` path must not interfere with the success
        case."""
        instance = _BaiTestModel.bai_validate({"name": "ok", "count": 1})
        assert isinstance(instance, _BaiTestModel)
        assert instance.name == "ok"
        assert instance.count == 1

    def test_bai_validate_raises_configured_domain_error(self) -> None:
        """An invalid payload raises the domain class registered via
        ``__bai_error_class__`` (here :class:`InvalidResourceOpts`)
        with structured field-error data attached, instead of letting
        the raw ``ValidationError`` bubble up."""
        with pytest.raises(InvalidResourceOpts) as excinfo:
            _BaiTestModel.bai_validate({"count": "not-a-number"})

        err = excinfo.value
        assert isinstance(err, web.HTTPBadRequest)
        assert err.extra_msg is not None
        assert err.extra_data is not None
        locs = {e["loc"] for e in err.extra_data["errors"]}
        assert "name" in locs
        assert "count" in locs

    def test_bai_validate_requires_error_class(self) -> None:
        """A subclass that forgets to set ``__bai_error_class__`` gets
        a clear ``NotImplementedError`` instead of a confusing
        attribute error — surfaces the missing wiring at first call."""

        class _Forgotten(BackendAIModel):
            value: int

        with pytest.raises(NotImplementedError) as excinfo:
            _Forgotten.bai_validate({"value": 1})
        assert "_Forgotten" in str(excinfo.value)
