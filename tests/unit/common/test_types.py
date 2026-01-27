import asyncio
from decimal import Decimal

import pytest
from typeguard import TypeCheckError

from ai.backend.common.types import (
    BinarySize,
    DefaultForUnspecified,
    HardwareMetadata,
    MetricValue,
    ResourceSlot,
    SlotName,
    SlotTypes,
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
    # As of 24.09, check_typed_dict() is a mere alias of typeguard.check_type().
    with pytest.raises(TypeError):  # the second arg is not hashable
        check_typed_dict({}, {})
    check_typed_dict({}, dict)
    with pytest.raises(TypeCheckError):
        check_typed_dict({}, int)
    with pytest.raises(TypeCheckError):
        check_typed_dict({}, HardwareMetadata)
    with pytest.raises(TypeCheckError):
        check_typed_dict({"status": "oops", "status_info": None, "metadata": {}}, HardwareMetadata)
    with pytest.raises(TypeCheckError):
        check_typed_dict(
            {"status": "healthy", "status_info": None, "metadata": {"a": 1}}, HardwareMetadata
        )

    a = check_typed_dict(
        {"status": "healthy", "status_info": None, "metadata": {"a": "b"}}, HardwareMetadata
    )
    assert isinstance(a, dict)


def test_binary_size_str_conversion():
    assert BinarySize.from_str("1 byte") == 1
    assert BinarySize.from_str(19291991) == 19291991
    with pytest.raises(ValueError):
        BinarySize.from_str("1.1")
    assert BinarySize.from_str("1.1k") == 1126
    assert BinarySize.from_str("11_021_204") == 11021204
    assert BinarySize.from_str("12345 bytes") == 12345
    assert BinarySize.from_str("12345 B") == 12345
    assert BinarySize.from_str("12_345 bytes") == 12345
    assert BinarySize.from_str("99 bytes") == 99
    assert BinarySize.from_str("1 KiB") == 1024
    assert BinarySize.from_str("2 KiBytes") == 2048
    assert BinarySize.from_str("124.32 KiB") == 127303
    assert str(BinarySize(1)) == "1 byte"
    assert str(BinarySize(2)) == "2 bytes"
    assert str(BinarySize(1024)) == "1 KiB"
    assert str(BinarySize(2048)) == "2 KiB"
    assert str(BinarySize(105935)) == "103.45 KiB"
    assert str(BinarySize(127303)) == "124.32 KiB"
    assert str(BinarySize(1048576)) == "1 MiB"
    # If we don't apply ":f" when stringifying decimals, 1048576123 would produce "1E+3"
    assert str(BinarySize(1048576123)) == "1000 MiB"

    x = BinarySize.from_str("inf")
    assert isinstance(x, Decimal)
    assert x.is_infinite()
    with pytest.raises(ValueError):
        BinarySize.finite_from_str("inf")

    # short-hand formats
    assert BinarySize.from_str("1g") == 2**30
    assert BinarySize.from_str("1m") == 1048576
    assert BinarySize.from_str("0.5m") == 524288
    assert BinarySize.from_str("512k") == 524288
    assert f"{BinarySize(930): }" == "930"
    assert f"{BinarySize(1024):k}" == "1k"  # type: ignore
    assert f"{BinarySize(524288):k}" == "512k"  # type: ignore
    assert f"{BinarySize(1048576):k}" == "1024k"  # type: ignore
    assert f"{BinarySize(524288):m}" == "0.5m"  # type: ignore
    assert f"{BinarySize(1048576):m}" == "1m"  # type: ignore
    assert f"{BinarySize(1048576123):m}" == "1000m"  # type: ignore
    assert f"{BinarySize(2**30):g}" == "1g"
    with pytest.raises(ValueError):
        f"{BinarySize(1):x}"
    with pytest.raises(ValueError):
        f"{BinarySize(1):qqqq}"
    with pytest.raises(ValueError):
        f"{BinarySize(1)}"
    assert f"{BinarySize(930):s}" == "930"
    assert f"{BinarySize(1024):s}" == "1k"
    assert f"{BinarySize(524288):s}" == "512k"
    assert f"{BinarySize(1048576):s}" == "1m"
    assert f"{BinarySize(2**30):s}" == "1g"


def test_binary_size_decimal_conversion():
    assert Decimal(BinarySize(1)) == 1
    assert Decimal(BinarySize(2)) == 2
    assert Decimal(BinarySize(1024)) == 1024
    assert Decimal(BinarySize(2048)) == 2048
    assert Decimal(BinarySize(105935)) == 105935
    assert Decimal(BinarySize(127303)) == 127303


def test_slot_name_parsing() -> None:
    s = SlotName("cuda.shares")
    assert s.is_accelerator()
    assert s.device_name == "cuda"
    assert s.major_type == "shares"
    assert s.minor_type == ""
    s = SlotName("cuda.device")
    assert s.is_accelerator()
    assert s.device_name == "cuda"
    assert s.major_type == "device"
    assert s.minor_type == ""
    s = SlotName("cpu")
    assert not s.is_accelerator()
    assert s.device_name == "cpu"
    assert s.major_type == ""
    assert s.minor_type == ""
    s = SlotName("mem")
    assert not s.is_accelerator()
    assert s.device_name == "mem"
    assert s.major_type == ""
    assert s.minor_type == ""
    s = SlotName("cuda.device:mig-10g")
    assert s.is_accelerator()
    assert s.device_name == "cuda"
    assert s.major_type == "device"
    assert s.minor_type == "mig-10g"


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


def test_resource_slot_parsing_typeless_user_input():
    # slot names containing "mem" are assumed as BinarySize if no explicit type table is given
    r1 = ResourceSlot.from_user_input({"a": "1", "cuda.mem": "2g"}, None)
    assert r1["a"] == Decimal(1)
    assert r1["cuda.mem"] == Decimal(2 * (2**30))

    r1 = ResourceSlot.from_user_input({"a": "inf", "cuda.mem": "inf"}, None)
    assert r1["a"].is_infinite()
    assert r1["cuda.mem"].is_infinite()

    with pytest.raises(ValueError, match="Cannot convert"):
        r1 = ResourceSlot.from_user_input({"a": "1", "cuda.smp": "2g"}, None)

    r1 = ResourceSlot.from_user_input({"a": "inf", "cuda.smp": "inf"}, None)
    assert r1["a"].is_infinite()
    assert r1["cuda.smp"].is_infinite()


def test_resource_slot_parsing_typeless_user_input_serialize_again():
    # slot names containing "mem" are assumed as BinarySize if no explicit type table is given
    r1 = ResourceSlot.from_user_input({"a": "1", "cuda.mem": "2g"}, None)
    assert r1["a"] == Decimal(1)
    assert r1["cuda.mem"] == Decimal(2 * (2**30))

    s1 = r1.to_json()
    # when serialized again, now the "cuda.mem" is an expanded integer
    # (i.e., saving into database)
    print(s1)

    # now we can use `from_json()` safely
    # (i.e., loaded from database)
    r2 = ResourceSlot.from_json(s1)
    assert r2 == r1


def test_resource_slot_parsing_typeless_user_input_serialize_again_2():
    with pytest.raises(ValueError, match="Unknown slot type"):
        ResourceSlot.from_user_input(
            {"a": "1", "shmem": "2g"},
            {
                SlotName("a"): SlotTypes("count"),
                SlotName("mem"): SlotTypes("bytes"),
                # missing "shmem": should raise an unknown slot error
            },
        )


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


class TestMetricValue:
    def test_legacy_dict_validation(self) -> None:
        legacy = {
            "current": "100.000",
            "capacity": "1000.000",
            "pct": "10.00",
            "unit_hint": "bytes",
            "stats.min": "50.000",
            "stats.max": "200.000",
            "stats.sum": "500.000",
            "stats.avg": "100.000",
            "stats.diff": "50.000",
            "stats.rate": "10.000",
        }
        mv = MetricValue.model_validate(legacy)
        assert mv.current == "100.000"
        assert mv.capacity == "1000.000"
        assert mv.pct == "10.00"
        assert mv.unit_hint == "bytes"
        assert mv.stats_min == "50.000"
        assert mv.stats_max == "200.000"
        assert mv.stats_sum == "500.000"
        assert mv.stats_avg == "100.000"
        assert mv.stats_diff == "50.000"
        assert mv.stats_rate == "10.000"

    def test_serialization_preserves_alias(self) -> None:
        mv = MetricValue(
            current="100",
            pct="10.00",
            unit_hint="bytes",
            stats_min="50",
            stats_max="200",
        )
        data = mv.model_dump(by_alias=True, exclude_none=True)
        assert "stats.min" in data
        assert "stats.max" in data
        assert "stats_min" not in data
        assert "stats_max" not in data
        assert data["stats.min"] == "50"
        assert data["stats.max"] == "200"

    def test_partial_stats_fields(self) -> None:
        partial = {
            "current": "100",
            "pct": "10.00",
            "unit_hint": "bytes",
            "stats.max": "200",
        }
        mv = MetricValue.model_validate(partial)
        assert mv.stats_max == "200"
        assert mv.stats_min is None
        assert mv.stats_sum is None
        assert mv.stats_avg is None

    def test_appproxy_type_field(self) -> None:
        with_type = {
            "current": "100",
            "pct": "10.00",
            "unit_hint": "bytes",
            "__type": "GAUGE",
        }
        mv = MetricValue.model_validate(with_type)
        assert mv.type_ == "GAUGE"

        data = mv.model_dump(by_alias=True, exclude_none=True)
        assert "__type" in data
        assert data["__type"] == "GAUGE"
        assert "type_" not in data

    def test_round_trip_serialization(self) -> None:
        original = {
            "current": "100.000",
            "capacity": "1000.000",
            "pct": "10.00",
            "unit_hint": "bytes",
            "stats.min": "50.000",
            "stats.max": "200.000",
        }
        mv = MetricValue.model_validate(original)
        serialized = mv.model_dump(by_alias=True, exclude_none=True)
        mv2 = MetricValue.model_validate(serialized)

        assert mv.current == mv2.current
        assert mv.capacity == mv2.capacity
        assert mv.pct == mv2.pct
        assert mv.unit_hint == mv2.unit_hint
        assert mv.stats_min == mv2.stats_min
        assert mv.stats_max == mv2.stats_max
