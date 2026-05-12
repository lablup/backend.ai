from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from aiohttp import web
from multidict import CIMultiDict

from ai.backend.client.session import AsyncSession as APISession
from ai.backend.web.proxy import _pass_through_date_header


def _frontend_request(headers: dict[str, str]) -> web.Request:
    """Cheap stand-in for `aiohttp.web.Request` — only `.headers` is read."""
    return cast(web.Request, SimpleNamespace(headers=CIMultiDict(headers)))


def _api_session(*, is_anonymous: bool) -> APISession:
    """Stand-in exposing only the fields `_pass_through_date_header` reads."""
    return cast(
        APISession,
        SimpleNamespace(config=SimpleNamespace(is_anonymous=is_anonymous)),
    )


CLIENT_DATE = "Tue, 02 Sep 2025 08:00:00 GMT"


def test_anonymous_session_with_date_forwards_it() -> None:
    overrides = _pass_through_date_header(
        _frontend_request({"Date": CLIENT_DATE}),
        _api_session(is_anonymous=True),
    )
    assert overrides == {"Date": CLIENT_DATE}


def test_anonymous_session_without_date_returns_empty() -> None:
    overrides = _pass_through_date_header(
        _frontend_request({}),
        _api_session(is_anonymous=True),
    )
    assert overrides == {}


def test_authenticated_session_does_not_forward_date() -> None:
    # Critical: in the re-signing path the proxy signs with its own keypair,
    # so the client must NOT be allowed to dictate the timestamp on the wire.
    overrides = _pass_through_date_header(
        _frontend_request({"Date": CLIENT_DATE}),
        _api_session(is_anonymous=False),
    )
    assert overrides == {}
