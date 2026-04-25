"""Cursor encoding/decoding utilities shared by GQL and REST adapters."""

from __future__ import annotations

import uuid

from graphql_relay.utils import base64, unbase64

from ai.backend.manager.errors.api import InvalidCursor

CURSOR_VERSION = "v1"


def encode_cursor(row_id: str | uuid.UUID) -> str:
    """Encode row ID to cursor format: base64(cursor:v1:{row_id})"""
    raw = f"cursor:{CURSOR_VERSION}:{row_id}"
    return base64(raw)


def decode_cursor(cursor: str) -> str:
    """Decode cursor and return row_id. Raises InvalidCursor on failure."""
    try:
        raw = unbase64(cursor)
    except Exception as e:
        raise InvalidCursor(f"Invalid cursor encoding: {cursor}") from e

    parts = raw.split(":", 2)
    if len(parts) != 3 or parts[0] != "cursor" or parts[1] != CURSOR_VERSION:
        raise InvalidCursor(f"Invalid cursor format: {cursor}")
    return parts[2]  # row_id
