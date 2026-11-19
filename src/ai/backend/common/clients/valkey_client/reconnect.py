from __future__ import annotations

from typing import override

from glide import ClosingError, RequestError
from glide import ConnectionError as GlideConnectionError

from ai.backend.common.exception import ClientNotConnectedError, ValkeyRoleMismatchError
from ai.backend.common.resilience.policies.retry import ReconnectErrorClassifier


class ValkeyReconnectErrorClassifier(ReconnectErrorClassifier):
    """Judges connection loss and leader change errors of Valkey."""

    @override
    def is_reconnect_error(self, error: BaseException) -> bool:
        if isinstance(
            error,
            (
                GlideConnectionError,
                ClosingError,
                ClientNotConnectedError,
                ValkeyRoleMismatchError,
            ),
        ):
            return True
        return isinstance(error, RequestError) and str(error).startswith("READONLY")
