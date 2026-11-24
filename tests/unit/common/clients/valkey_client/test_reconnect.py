from __future__ import annotations

import pytest
from glide import ClosingError, RequestError
from glide import ConnectionError as GlideConnectionError
from glide import TimeoutError as GlideTimeoutError

from ai.backend.common.clients.valkey_client.reconnect import ValkeyReconnectErrorClassifier
from ai.backend.common.exception import ClientNotConnectedError, ValkeyRoleMismatchError

RECONNECT_ERRORS: list[tuple[str, BaseException]] = [
    ("glide connection error", GlideConnectionError("x")),
    ("glide closing error", ClosingError("x")),
    ("readonly reply", RequestError("READONLY You can't write against a read only replica.")),
    ("client not connected", ClientNotConnectedError()),
    ("role mismatch", ValkeyRoleMismatchError()),
]

NON_RECONNECT_ERRORS: list[tuple[str, BaseException]] = [
    ("other request error", RequestError("WRONGTYPE Operation against a key")),
    ("glide timeout", GlideTimeoutError("x")),
    ("value error", ValueError("x")),
]


class TestValkeyReconnectErrorClassifier:
    @pytest.mark.parametrize(
        "error", [e for _, e in RECONNECT_ERRORS], ids=[n for n, _ in RECONNECT_ERRORS]
    )
    def test_reconnect_errors(self, error: BaseException) -> None:
        assert ValkeyReconnectErrorClassifier().is_reconnect_error(error) is True

    @pytest.mark.parametrize(
        "error", [e for _, e in NON_RECONNECT_ERRORS], ids=[n for n, _ in NON_RECONNECT_ERRORS]
    )
    def test_non_reconnect_errors(self, error: BaseException) -> None:
        assert ValkeyReconnectErrorClassifier().is_reconnect_error(error) is False
