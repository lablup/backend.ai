"""Tests for ai.backend.common.dto.manager.v2.common shared DTOs."""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.common import BinarySizeInfo

# Byte sizes that overflow GraphQL Int (32-bit signed, max 2,147,483,647)
# and JSON-number-safe integers (2^53). These must serialize as strings.
_OVER_2GIB = "1234000000000"
_OVER_2POW53 = str(2**53 + 1)


class TestBinarySizeInfo:
    """BinarySizeInfo.expr is a decimal byte-count string, unbounded by Int range."""

    def test_expr_is_string(self) -> None:
        info = BinarySizeInfo(expr="1073741824", display="1g")
        assert info.expr == "1073741824"

    def test_rejects_int_expr(self) -> None:
        int_value: Any = 1073741824
        with pytest.raises(ValidationError):
            BinarySizeInfo(expr=int_value, display="1g")

    @pytest.mark.parametrize("byte_str", [_OVER_2GIB, _OVER_2POW53])
    def test_serializes_large_values_as_json_string(self, byte_str: str) -> None:
        info = BinarySizeInfo(expr=byte_str, display="humanized")
        payload = json.loads(info.model_dump_json())
        assert payload["expr"] == byte_str
        assert isinstance(payload["expr"], str)

    @pytest.mark.parametrize("byte_str", [_OVER_2GIB, _OVER_2POW53])
    def test_round_trip_preserves_large_values(self, byte_str: str) -> None:
        info = BinarySizeInfo(expr=byte_str, display="humanized")
        restored = BinarySizeInfo.model_validate_json(info.model_dump_json())
        assert restored.expr == byte_str
        # Exact byte count is recoverable as an arbitrary-precision int.
        assert int(restored.expr) == int(byte_str)
