from __future__ import annotations

import pytest
from aiohttp import web
from pydantic import BaseModel, ValidationError

from ai.backend.common.exception import ErrorDetail, ErrorDomain, ErrorOperation
from ai.backend.manager.errors.kernel import InvalidSessionCreationConfig


class _DummyConfig(BaseModel):
    """Stand-in for a real ``CreationConfigVN`` so the test does not
    depend on the full session-creation schema."""

    image: str
    cluster_size: int


class TestInvalidSessionCreationConfig:
    """Pinning the wire contract of one representative domain error
    class (used by the V1-V7 ``CreationConfig`` wraps in
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
        """``from_pydantic`` must wrap a ``ValidationError`` so the
        response body still names the offending field — that is the
        whole point of the per-domain wrapping introduced by this PR."""
        try:
            _DummyConfig.model_validate({"cluster_size": "not-a-number"})
        except ValidationError as exc:
            err = InvalidSessionCreationConfig.from_pydantic(exc)
        else:
            pytest.fail("Expected ValidationError")

        # Human-readable summary must mention each missing/invalid field
        # under the default ``config`` prefix.
        assert err.extra_msg is not None
        assert "config.image" in err.extra_msg
        assert "config.cluster_size" in err.extra_msg

        # Structured payload preserves every error so clients can render
        # per-field messages without re-parsing the summary string.
        assert err.extra_data is not None
        errors = err.extra_data["errors"]
        locs = {e["loc"] for e in errors}
        assert "config.image" in locs
        assert "config.cluster_size" in locs
