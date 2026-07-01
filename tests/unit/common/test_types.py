import asyncio
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest
from typeguard import TypeCheckError

from ai.backend.common.exception import (
    BackendAISchemaValidationFailed,
    InvalidResourceSlotQuantity,
    UnknownResourceSlotType,
)
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import (
    BinarySize,
    DefaultForUnspecified,
    HardwareMetadata,
    MountInfoEntry,
    MountPermission,
    ResourceSlot,
    ResourceSlotEntry,
    SlotName,
    SlotTypes,
    _stringify_number,
    aobject,
    check_typed_dict,
)


async def test_aobject() -> None:
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


def test_check_typed_dict() -> None:
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


def test_binary_size_str_conversion() -> None:
    assert BinarySize.from_str("1 byte") == 1
    # MyPy doesn't support numbers.Integral for static type checking
    # The function accepts int which is a numbers.Integral, so we can safely ignore this
    assert BinarySize.from_str(19291991) == 19291991  # type: ignore[arg-type]
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
    assert f"{BinarySize(1024):k}" == "1k"
    assert f"{BinarySize(524288):k}" == "512k"
    assert f"{BinarySize(1048576):k}" == "1024k"
    assert f"{BinarySize(524288):m}" == "0.5m"
    assert f"{BinarySize(1048576):m}" == "1m"
    assert f"{BinarySize(1048576123):m}" == "1000m"
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


def test_binary_size_decimal_conversion() -> None:
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


def test_resource_slot_serialization() -> None:
    # from_user_input() and from_policy() takes the explicit slot type information to
    # convert human-readable values to raw decimal values,
    # while from_json() treats those values as stringified decimal expressions "as-is".

    # from_user_input expects Mapping[SlotName, SlotTypes]
    st_user_input: dict[SlotName, SlotTypes] = {
        SlotName("a"): SlotTypes("count"),
        SlotName("b"): SlotTypes("bytes"),
    }
    r1 = ResourceSlot.from_user_input({"a": "1", "b": "2g"}, st_user_input)
    r2 = ResourceSlot.from_user_input({"a": "2", "b": "1g"}, st_user_input)
    r3 = ResourceSlot.from_user_input({"a": "1"}, st_user_input)
    with pytest.raises(UnknownResourceSlotType):
        ResourceSlot.from_user_input({"x": "1"}, st_user_input)

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

    # to_humanized expects Mapping[str, Any] (plain string keys)
    st_humanized: dict[str, str] = {"a": "count", "b": "bytes"}
    assert r1.to_humanized(st_humanized) == {"a": "1", "b": "2g"}
    assert r2.to_humanized(st_humanized) == {"a": "2", "b": "1g"}
    assert r3.to_humanized(st_humanized) == {"a": "1", "b": "0"}
    assert r1 == ResourceSlot.from_json({"a": "1", "b": "2147483648"})
    assert r2 == ResourceSlot.from_json({"a": "2", "b": "1073741824"})
    assert r3 == ResourceSlot.from_json({"a": "1", "b": "0"})

    r4 = ResourceSlot.from_user_input(
        {"a": Decimal("Infinity"), "b": Decimal("-Infinity")}, st_user_input
    )
    assert not r4["a"].is_finite()
    assert not r4["b"].is_finite()
    assert r4["a"] > 0
    assert r4["b"] < 0
    assert r4.to_humanized(st_humanized) == {"a": "Infinity", "b": "-Infinity"}

    # The result for "unspecified" fields may be different
    # depending on the policy options.

    # from_policy expects Mapping[str, Any] (plain string keys)
    st_policy: dict[str, str] = {"a": "count", "b": "bytes"}
    r1 = ResourceSlot.from_policy(
        {
            "total_resource_slots": {"a": "10"},
            "default_for_unspecified": DefaultForUnspecified.UNLIMITED,
        },
        st_policy,
    )
    assert r1["a"] == Decimal(10)
    assert r1["b"] == Decimal("Infinity")
    r2 = ResourceSlot.from_policy(
        {
            "total_resource_slots": {"a": "10"},
            "default_for_unspecified": DefaultForUnspecified.LIMITED,
        },
        st_policy,
    )
    assert r2["a"] == Decimal(10)
    assert r2["b"] == Decimal(0)


def test_resource_slot_serialization_prevent_scientific_notation() -> None:
    r1 = ResourceSlot({"a": "2E+1", "b": "200"})
    assert r1.to_json()["a"] == "20"
    assert r1.to_json()["b"] == "200"


def test_resource_slot_serialization_filter_null() -> None:
    r1 = ResourceSlot({"a": "1", "x": None})
    assert r1.to_json()["a"] == "1"
    assert "x" not in r1.to_json()


def test_resource_slot_parsing_typeless_user_input() -> None:
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


def test_resource_slot_parsing_typeless_user_input_serialize_again() -> None:
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


def test_resource_slot_parsing_typeless_user_input_serialize_again_2() -> None:
    with pytest.raises(UnknownResourceSlotType, match="Unknown slot type"):
        ResourceSlot.from_user_input(
            {"a": "1", "shmem": "2g"},
            {
                SlotName("a"): SlotTypes("count"),
                SlotName("mem"): SlotTypes("bytes"),
                # missing "shmem": should raise an unknown slot error
            },
        )


def test_resource_slot_rejects_negative_count() -> None:
    with pytest.raises(InvalidResourceSlotQuantity, match="cannot be negative"):
        ResourceSlot.from_user_input({"cpu": "-1"}, None)
    with pytest.raises(InvalidResourceSlotQuantity, match="cannot be negative"):
        ResourceSlot.from_user_input({"cpu": -1}, None)


def test_resource_slot_rejects_negative_bytes() -> None:
    with pytest.raises(InvalidResourceSlotQuantity, match="cannot be negative"):
        ResourceSlot.from_user_input({"mem": Decimal(-1)}, None)
    with pytest.raises(InvalidResourceSlotQuantity, match="cannot be negative"):
        ResourceSlot.from_user_input({"mem": -1}, None)


def test_resource_slot_rejects_negative_with_typed_slots() -> None:
    with pytest.raises(InvalidResourceSlotQuantity, match="cannot be negative"):
        ResourceSlot.from_user_input(
            {"cpu": "-2"},
            {SlotName("cpu"): SlotTypes("count")},
        )


def test_resource_slot_comparison_simple_equality() -> None:
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


def test_resource_slot_comparison_ordering() -> None:
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


def test_resource_slot_comparison_ordering_reverse() -> None:
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


def test_resource_slot_comparison_subset() -> None:
    r1 = ResourceSlot.from_json({"a": "3", "b": "200"})
    r3 = ResourceSlot.from_json({"a": "3"})
    assert r3.eq_contained(r1)
    assert not r3.eq_contains(r1)
    assert not r1.eq_contained(r3)
    assert r1.eq_contains(r3)


def test_resource_slot_calc_with_infinity() -> None:
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


def test_stringify_number_decimal_places() -> None:
    # Regression test: fGPU values should not show 6 decimal places (BA-4840)
    assert _stringify_number(Decimal("1.000000")) == "1"
    assert _stringify_number(Decimal("1.500000")) == "1.5"
    assert _stringify_number(Decimal("1.250000")) == "1.25"
    assert _stringify_number(Decimal("0.250000")) == "0.25"
    assert _stringify_number(Decimal("0.000000")) == "0"
    assert _stringify_number(Decimal("10.000000")) == "10"
    # Values with more than 2 decimal places are rounded to 2
    assert _stringify_number(Decimal("1.234567")) == "1.23"
    # Infinity handling unchanged
    assert _stringify_number(float("inf")) == "Infinity"
    assert _stringify_number(float("-inf")) == "-Infinity"
    # Integer and BinarySize handling unchanged
    assert _stringify_number(42) == "42"
    assert _stringify_number(BinarySize(1024)) == "1024"


@dataclass(frozen=True)
class _LegacyDecodingCase:
    """Pairs a raw JSONB shape with the canonical entry it should decode to."""

    raw_payload: dict[str, Any]
    expected: MountInfoEntry


_FOLDER_UUID = uuid.uuid4()
_QUOTA_SCOPE_STR = f"user:{uuid.uuid4().hex}"


class TestMountPermissionExceeds:
    @pytest.mark.parametrize(
        ("requested", "other", "expected"),
        [
            (MountPermission.READ_WRITE, MountPermission.READ_ONLY, True),
            (MountPermission.RW_DELETE, MountPermission.READ_WRITE, True),
            (MountPermission.RW_DELETE, MountPermission.READ_ONLY, True),
            (MountPermission.READ_ONLY, MountPermission.READ_ONLY, False),
            (MountPermission.READ_ONLY, MountPermission.READ_WRITE, False),
            (MountPermission.READ_WRITE, MountPermission.RW_DELETE, False),
        ],
    )
    def test_exceeds(
        self,
        requested: MountPermission,
        other: MountPermission,
        expected: bool,
    ) -> None:
        assert requested.exceeds(other) is expected


class TestMountInfoEntryLegacyShape:
    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _LegacyDecodingCase(
                    raw_payload={
                        "name": ".claude",
                        "vfid": f"{_QUOTA_SCOPE_STR}/{_FOLDER_UUID.hex}",
                        "vfsubpath": ".",
                        "host_path": "/vfroot/local/user:00/abc",
                        "kernel_path": "/home/work/.claude",
                        "mount_perm": "rw",
                        "usage_mode": "general",
                    },
                    expected=MountInfoEntry(
                        vfolder_id=VFolderUUID(_FOLDER_UUID),
                        mount_destination="/home/work/.claude",
                        mount_perm=MountPermission.READ_WRITE,
                        subpath=".",
                    ),
                ),
                id="legacy_vfid_with_quota_scope_prefix",
            ),
            pytest.param(
                _LegacyDecodingCase(
                    raw_payload={
                        "vfid": _FOLDER_UUID.hex,
                        "kernel_path": "/home/work/data",
                        "mount_perm": "ro",
                    },
                    expected=MountInfoEntry(
                        vfolder_id=VFolderUUID(_FOLDER_UUID),
                        mount_destination="/home/work/data",
                        mount_perm=MountPermission.READ_ONLY,
                        subpath=None,
                    ),
                ),
                id="legacy_vfid_without_quota_scope_prefix",
            ),
            pytest.param(
                _LegacyDecodingCase(
                    raw_payload={
                        "vfolder_id": str(_FOLDER_UUID),
                        "mount_destination": "/home/work/data",
                        "mount_perm": "rw",
                        "subpath": "nested/dir",
                    },
                    expected=MountInfoEntry(
                        vfolder_id=VFolderUUID(_FOLDER_UUID),
                        mount_destination="/home/work/data",
                        mount_perm=MountPermission.READ_WRITE,
                        subpath="nested/dir",
                    ),
                ),
                id="new_shape_unchanged",
            ),
            pytest.param(
                _LegacyDecodingCase(
                    raw_payload={
                        "vfid": _FOLDER_UUID.hex,
                        "kernel_path": "/home/work/data",
                        "vfsubpath": "weights",
                        "mount_perm": "rw",
                    },
                    expected=MountInfoEntry(
                        vfolder_id=VFolderUUID(_FOLDER_UUID),
                        mount_destination="/home/work/data",
                        mount_perm=MountPermission.READ_WRITE,
                        subpath="weights",
                    ),
                ),
                id="vfsubpath_alias_maps_to_subpath",
            ),
        ],
    )
    async def test_decodes_payload_to_canonical_entry(
        self,
        case: _LegacyDecodingCase,
    ) -> None:
        assert MountInfoEntry.model_validate(case.raw_payload) == case.expected

    async def test_missing_vfolder_id_and_vfid_still_fails(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            MountInfoEntry.model_validate({
                "mount_destination": "/home/work/data",
                "mount_perm": "rw",
            })


@dataclass(frozen=True)
class _QuantityCase:
    """Pairs a resource entry quantity with the slot value it should parse to."""

    resource_type: str
    quantity: str
    expected: Decimal


class TestResourceSlotEntryToResourceSlot:
    """``ResourceSlotEntry.to_resource_slot`` quantity parsing (BA-6576)."""

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(_QuantityCase("cpu", "2", Decimal("2")), id="plain-int"),
            pytest.param(_QuantityCase("cpu", "0.5", Decimal("0.5")), id="fraction"),
            pytest.param(
                _QuantityCase("mem", "4294967296", Decimal("4294967296")), id="bytes-decimal"
            ),
            pytest.param(
                _QuantityCase("mem", "4g", Decimal(BinarySize.from_str("4g"))),
                id="human-readable-size",
            ),
        ],
    )
    def test_valid_quantity_is_parsed(self, case: _QuantityCase) -> None:
        """Plain decimals and human-readable sizes such as ``"4g"`` for a memory
        slot are parsed with BinarySize tolerance, matching the legacy enqueue
        path, instead of raising and surfacing as a 500."""
        entries = [ResourceSlotEntry(resource_type=case.resource_type, quantity=case.quantity)]
        assert ResourceSlotEntry.inputs_to_resource_slot(entries) == ResourceSlot({
            case.resource_type: case.expected
        })

    @pytest.mark.parametrize(
        ("resource_type", "quantity"),
        [
            pytest.param("mem", "not-a-number", id="garbage"),
            pytest.param("cpu", "abc", id="non-numeric"),
            pytest.param("mem", "", id="empty"),
            pytest.param("cpu", "-1", id="negative"),
        ],
    )
    def test_invalid_quantity_raises_4xx(self, resource_type: str, quantity: str) -> None:
        """A non-parseable or negative quantity is rejected with a 4xx
        ``InvalidResourceSlotQuantity`` (BackendAIError) rather than letting
        ``decimal.InvalidOperation`` propagate as an unhandled 500."""
        entries = [ResourceSlotEntry(resource_type=resource_type, quantity=quantity)]
        with pytest.raises(InvalidResourceSlotQuantity):
            ResourceSlotEntry.inputs_to_resource_slot(entries)

    def test_multiple_entries_are_merged(self) -> None:
        entries = [
            ResourceSlotEntry(resource_type="cpu", quantity="2"),
            ResourceSlotEntry(resource_type="mem", quantity="4g"),
        ]
        assert ResourceSlotEntry.inputs_to_resource_slot(entries) == ResourceSlot({
            "cpu": Decimal("2"),
            "mem": Decimal(BinarySize.from_str("4g")),
        })

    def test_empty_entries(self) -> None:
        assert ResourceSlotEntry.inputs_to_resource_slot([]) == ResourceSlot()
