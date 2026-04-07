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
