import asyncio
from decimal import Decimal

import pytest

from ai.backend.common.types import (
    BinarySize,
    DefaultForUnspecified,
    HardwareMetadata,
    ResourceSlot,
    aobject,
    check_typed_dict,
)


@pytest.mark.asyncio
async def test_aobject():
    init_count = 0
    ainit_count = 0

    class MyBase(aobject):
        def __init__(self, x: int) -> None:
            nonlocal init_count
            init_count += 1
            self.x = x

        async def __ainit__(self) -> None:
            await asyncio.sleep(0.01)
            nonlocal ainit_count
            ainit_count += 1

    class MyDerived(MyBase):
        def __init__(self, x: int, y: int) -> None:
            super().__init__(x)
            nonlocal init_count
            init_count += 1
            self.y = y

        async def __ainit__(self) -> None:
            await super().__ainit__()
            await asyncio.sleep(0.01)
            nonlocal ainit_count
            ainit_count += 1

    init_count = 0
    ainit_count = 0
    o = await MyBase.new(1)
    assert o.x == 1
    assert init_count == 1
    assert ainit_count == 1

    init_count = 0
    ainit_count = 0
    o = await MyDerived.new(2, 3)
    assert o.x == 2
    assert o.y == 3
    assert init_count == 2
    assert ainit_count == 2


def test_check_typed_dict():
    with pytest.raises(TypeError):
        check_typed_dict({}, {})
    with pytest.raises(AssertionError):
        check_typed_dict({}, dict)
    with pytest.raises(AssertionError):
        check_typed_dict({}, int)
    with pytest.raises(TypeError):
        check_typed_dict({}, HardwareMetadata)
    with pytest.raises(TypeError):
        check_typed_dict({"status": "oops", "status_info": None, "metadata": {}}, HardwareMetadata)
    with pytest.raises(TypeError):
        check_typed_dict(
            {"status": "healthy", "status_info": None, "metadata": {"a": 1}}, HardwareMetadata
        )

    a = check_typed_dict(
        {"status": "healthy", "status_info": None, "metadata": {"a": "b"}}, HardwareMetadata
    )
    assert isinstance(a, dict)


def test_binary_size():
    assert 1 == BinarySize.from_str("1 byte")
    assert 19291991 == BinarySize.from_str(19291991)
    with pytest.raises(ValueError):
        BinarySize.from_str("1.1")
    assert 1126 == BinarySize.from_str("1.1k")
    assert 11021204 == BinarySize.from_str("11_021_204")
    assert 12345 == BinarySize.from_str("12345 bytes")
    assert 12345 == BinarySize.from_str("12345 B")
    assert 12345 == BinarySize.from_str("12_345 bytes")
    assert 99 == BinarySize.from_str("99 bytes")
    assert 1024 == BinarySize.from_str("1 KiB")
    assert 2048 == BinarySize.from_str("2 KiBytes")
    assert 127303 == BinarySize.from_str("124.32 KiB")
    assert str(BinarySize(1)) == "1 byte"
    assert str(BinarySize(2)) == "2 bytes"
    assert str(BinarySize(1024)) == "1 KiB"
    assert str(BinarySize(2048)) == "2 KiB"
    assert str(BinarySize(105935)) == "103.45 KiB"
    assert str(BinarySize(127303)) == "124.32 KiB"
    assert str(BinarySize(1048576)) == "1 MiB"

    x = BinarySize.from_str("inf")
    assert isinstance(x, Decimal)
    assert x.is_infinite()
    with pytest.raises(ValueError):
        BinarySize.finite_from_str("inf")

    # short-hand formats
    assert 2**30 == BinarySize.from_str("1g")
    assert 1048576 == BinarySize.from_str("1m")
    assert 524288 == BinarySize.from_str("0.5m")
    assert 524288 == BinarySize.from_str("512k")
    assert "{: }".format(BinarySize(930)) == "930"
    assert "{:k}".format(BinarySize(1024)) == "1k"  # type: ignore
    assert "{:k}".format(BinarySize(524288)) == "512k"  # type: ignore
    assert "{:k}".format(BinarySize(1048576)) == "1024k"  # type: ignore
    assert "{:m}".format(BinarySize(524288)) == "0.5m"  # type: ignore
    assert "{:m}".format(BinarySize(1048576)) == "1m"  # type: ignore
    assert "{:g}".format(BinarySize(2**30)) == "1g"
    with pytest.raises(ValueError):
        "{:x}".format(BinarySize(1))
    with pytest.raises(ValueError):
        "{:qqqq}".format(BinarySize(1))
    with pytest.raises(ValueError):
        "{:}".format(BinarySize(1))
    assert "{:s}".format(BinarySize(930)) == "930"
    assert "{:s}".format(BinarySize(1024)) == "1k"
    assert "{:s}".format(BinarySize(524288)) == "512k"
    assert "{:s}".format(BinarySize(1048576)) == "1m"
    assert "{:s}".format(BinarySize(2**30)) == "1g"


def test_resource_slot_serialization():
    # from_user_input() and from_policy() takes the explicit slot type information to
    # convert human-readable values to raw decimal values,
    # while from_json() treats those values as stringified decimal expressions "as-is".

    st = {"a": "count", "b": "bytes"}
    r1 = ResourceSlot.from_user_input({"a": "1", "b": "2g"}, st)
    r2 = ResourceSlot.from_user_input({"a": "2", "b": "1g"}, st)
    r3 = ResourceSlot.from_user_input({"a": "1"}, st)
    with pytest.raises(ValueError):
        ResourceSlot.from_user_input({"x": "1"}, st)

    assert r1["a"] == Decimal(1)
    assert r2["a"] == Decimal(2)
    assert r3["a"] == Decimal(1)
    assert r1["b"] == Decimal(2 * (2**30))
    assert r2["b"] == Decimal(1 * (2**30))
    assert r3["b"] == Decimal(0)

    x = r2 - r3
    assert x["a"] == Decimal(1)
    assert x["b"] == Decimal(1 * (2**30))

    # Conversely, to_json() stringifies the decimal values as-is,
    # while to_humanized() takes the explicit slot type information
    # to generate human-readable strings.

    assert r1.to_json() == {"a": "1", "b": "2147483648"}
    assert r2.to_json() == {"a": "2", "b": "1073741824"}
    assert r3.to_json() == {"a": "1", "b": "0"}
    assert r1.to_humanized(st) == {"a": "1", "b": "2g"}
    assert r2.to_humanized(st) == {"a": "2", "b": "1g"}
    assert r3.to_humanized(st) == {"a": "1", "b": "0"}
    assert r1 == ResourceSlot.from_json({"a": "1", "b": "2147483648"})
    assert r2 == ResourceSlot.from_json({"a": "2", "b": "1073741824"})
    assert r3 == ResourceSlot.from_json({"a": "1", "b": "0"})

    r4 = ResourceSlot.from_user_input({"a": Decimal("Infinity"), "b": Decimal("-Infinity")}, st)
    assert not r4["a"].is_finite()
    assert not r4["b"].is_finite()
    assert r4["a"] > 0
    assert r4["b"] < 0
    assert r4.to_humanized(st) == {"a": "Infinity", "b": "-Infinity"}

    # The result for "unspecified" fields may be different
    # depending on the policy options.

    r1 = ResourceSlot.from_policy(
        {
            "total_resource_slots": {"a": "10"},
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
        },
        st,
    )
    assert r1["a"] == Decimal(10)
    assert r1["b"] == Decimal("Infinity")
    r2 = ResourceSlot.from_policy(
        {
            "total_resource_slots": {"a": "10"},
            "default_for_unspecified": DefaultForUnspecified.LIMITED,
        },
        st,
    )
    assert r2["a"] == Decimal(10)
    assert r2["b"] == Decimal(0)


def test_resource_slot_serialization_prevent_scientific_notation():
    r1 = ResourceSlot({"a": "2E+1", "b": "200"})
    assert r1.to_json()["a"] == "20"
    assert r1.to_json()["b"] == "200"


def test_resource_slot_serialization_filter_null():
    r1 = ResourceSlot({"a": "1", "x": None})
    assert r1.to_json()["a"] == "1"
    assert "x" not in r1.to_json()


def test_resource_slot_serialization_typeless():
    r1 = ResourceSlot.from_user_input({"a": "1", "cuda.mem": "2g"}, None)
    assert r1["a"] == Decimal(1)
    assert r1["cuda.mem"] == Decimal(2 * (2**30))

    r1 = ResourceSlot.from_user_input({"a": "inf", "cuda.mem": "inf"}, None)
    assert r1["a"].is_infinite()
    assert r1["cuda.mem"].is_infinite()

    with pytest.raises(ValueError):
        r1 = ResourceSlot.from_user_input({"a": "1", "cuda.smp": "2g"}, None)

    r1 = ResourceSlot.from_user_input({"a": "inf", "cuda.smp": "inf"}, None)
    assert r1["a"].is_infinite()
    assert r1["cuda.smp"].is_infinite()


def test_resource_slot_comparison_simple_equality():
    r1 = ResourceSlot.from_json({"a": "3", "b": "200"})
    r2 = ResourceSlot.from_json({"a": "4", "b": "100"})
    r3 = ResourceSlot.from_json({"a": "2"})
    r4 = ResourceSlot.from_json({"a": "1"})
    r5 = ResourceSlot.from_json({"b": "100", "a": "4"})
    assert r1 != r2
    assert r1 != r3
    assert r2 != r3
    assert r3 != r4
    assert r2 == r5


def test_resource_slot_comparison_ordering():
    r1 = ResourceSlot.from_json({"a": "3", "b": "200"})
    r2 = ResourceSlot.from_json({"a": "4", "b": "100"})
    r3 = ResourceSlot.from_json({"a": "2"})
    r4 = ResourceSlot.from_json({"a": "1"})
    assert not r2 < r1
    assert not r2 <= r1
    assert r4 < r1
    assert r4 <= r1
    assert r4["b"] == 0  # auto-sync of slots
    assert r3 < r1
    assert r3 <= r1
    assert r3["b"] == 0  # auto-sync of slots


def test_resource_slot_comparison_ordering_reverse():
    r1 = ResourceSlot.from_json({"a": "3", "b": "200"})
    r2 = ResourceSlot.from_json({"a": "4", "b": "100"})
    r3 = ResourceSlot.from_json({"a": "2"})
    r4 = ResourceSlot.from_json({"a": "1"})
    assert not r2 > r1
    assert not r2 >= r1
    assert r1 > r3
    assert r1 >= r3
    assert r3["b"] == 0  # auto-sync of slots
    assert r1 > r4
    assert r1 >= r4
    assert r4["b"] == 0  # auto-sync of slots


def test_resource_slot_comparison_subset():
    r1 = ResourceSlot.from_json({"a": "3", "b": "200"})
    r3 = ResourceSlot.from_json({"a": "3"})
    assert r3.eq_contained(r1)
    assert not r3.eq_contains(r1)
    assert not r1.eq_contained(r3)
    assert r1.eq_contains(r3)


def test_resource_slot_calc_with_infinity():
    r1 = ResourceSlot.from_json({"a": "Infinity"})
    r2 = ResourceSlot.from_json({"a": "3"})
    r3 = r1 - r2
    assert r3["a"] == Decimal("Infinity")
    r3 = r1 + r2
    assert r3["a"] == Decimal("Infinity")

    r4 = ResourceSlot.from_json({"b": "5"})
    r5 = r1 - r4
    assert r5["a"] == Decimal("Infinity")
    assert r5["b"] == -5
    r5 = r1 + r4
    assert r5["a"] == Decimal("Infinity")
    assert r5["b"] == 5
