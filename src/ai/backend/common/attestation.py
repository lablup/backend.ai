from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any, Final

from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

ATTESTATION_SOURCE: Final = "host-reported"
MAX_ATTESTATION_KEYS: Final = 16
MAX_ATTESTATION_STRING_LEN: Final = 256
MAX_ATTESTATION_BYTES: Final = 2048

_PRIMITIVES = (str, int, float, bool, type(None))


def _is_bounded(value: Any, *, nested: bool) -> bool:
    if isinstance(value, str):
        return len(value) <= MAX_ATTESTATION_STRING_LEN
    if isinstance(value, _PRIMITIVES):
        return True
    if nested and isinstance(value, Mapping):
        return len(value) <= MAX_ATTESTATION_KEYS and all(
            isinstance(key, str)
            and len(key) <= MAX_ATTESTATION_STRING_LEN
            and _is_bounded(item, nested=False)
            for key, item in value.items()
        )
    return False


def build_attestation_status(summary: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """
    Make the `status_data.attestation` value from what a runtime profile reported, or None.

    The summary is informational and unverified: `source` is always forced to
    "host-reported". A summary over the limits is dropped entirely, not trimmed.
    """
    if summary is None:
        return None
    body = {key: value for key, value in summary.items() if key != "source"}
    if len(body) > MAX_ATTESTATION_KEYS or not all(
        isinstance(key, str)
        and len(key) <= MAX_ATTESTATION_STRING_LEN
        and _is_bounded(value, nested=True)
        for key, value in body.items()
    ):
        log.warning("attestation summary dropped: unsupported shape")
        return None
    status = {**body, "source": ATTESTATION_SOURCE}
    if len(json.dumps(status).encode()) > MAX_ATTESTATION_BYTES:
        log.warning("attestation summary dropped: too large", limit_bytes=MAX_ATTESTATION_BYTES)
        return None
    return status
