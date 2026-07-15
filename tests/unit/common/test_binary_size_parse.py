"""Tests for BinarySize._parse_str fractional handling.

Regression: Numeric DB columns and Decimal arithmetic frequently produce
integer-equivalent strings with trailing zeros (e.g., "536870912.000000").
Before the fix BinarySize._parse_str rejected these as "Fractional bytes",
breaking inference deployment creation that reads preset_resource_slots
from a sa.Numeric column. The parser must accept integer-equivalent
fractional strings while still rejecting truly fractional values.
"""

from __future__ import annotations

import pytest

from ai.backend.common.types import BinarySize


class TestBinarySizeFractionalZeroParsing:
    @pytest.mark.parametrize(
        ("expr", "expected"),
        [
            ("536870912.000000", 536870912),
            ("1024.0", 1024),
            ("0.000", 0),
            ("1.000000K", 1024),
            ("2.0M", 2 * 1024 * 1024),
        ],
    )
    def test_integer_equivalent_decimals_are_accepted(self, expr: str, expected: int) -> None:
        # Numeric DB columns and Decimal arithmetic emit trailing zeros for
        # integer values; BinarySize must collapse them before parsing.
        assert int(BinarySize.from_str(expr)) == expected

    @pytest.mark.parametrize(
        "expr",
        ["1.5", "0.5", "1.25", "1.000001"],
    )
    def test_truly_fractional_values_are_rejected(self, expr: str) -> None:
        # Anything that cannot be losslessly cast to int must still raise.
        with pytest.raises(ValueError):
            BinarySize.from_str(expr)

    def test_plain_integer_passthrough(self) -> None:
        # Sanity check: regular integer strings continue to parse normally.
        assert int(BinarySize.from_str("1024")) == 1024
        assert int(BinarySize.from_str("1G")) == 1024 * 1024 * 1024


class TestBinarySizeToBytesStr:
    """to_bytes_str returns the exact byte count, bypassing the humanizing str()/format."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0, "0"),
            (1024, "1024"),
            (1073741824, "1073741824"),
            (1234000000000, "1234000000000"),  # > 2 GiB
            (2**53 + 1, "9007199254740993"),  # > JSON-safe int
        ],
    )
    def test_returns_exact_decimal_bytes(self, value: int, expected: str) -> None:
        assert BinarySize(value).to_bytes_str() == expected

    def test_does_not_humanize(self) -> None:
        # str()/format humanize; to_bytes_str must not.
        size = BinarySize(1073741824)
        assert str(size) == "1 GiB"
        assert f"{size:s}" == "1g"
        assert size.to_bytes_str() == "1073741824"


class TestBinarySizeToSizeInfo:
    """to_size_info builds a BinarySizeInfo (exact-bytes expr + humanized display)."""

    def test_zero_is_a_real_value(self) -> None:
        # A byte count of 0 must produce a DTO, not be mistaken for absent.
        info = BinarySize.to_size_info(0)
        assert info.expr == "0"
        assert info.display == "0"

    @pytest.mark.parametrize(
        ("value", "expected_expr"),
        [
            (1073741824, "1073741824"),
            (1234000000000, "1234000000000"),  # > 2 GiB
            (2**53 + 1, "9007199254740993"),  # > JSON-safe int
        ],
    )
    def test_expr_is_exact_decimal_bytes(self, value: int, expected_expr: str) -> None:
        assert BinarySize.to_size_info(value).expr == expected_expr

    def test_display_is_humanized(self) -> None:
        info = BinarySize.to_size_info(1073741824)
        assert info.expr == "1073741824"
        assert info.display == "1g"
