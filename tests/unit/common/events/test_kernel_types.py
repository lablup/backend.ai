from __future__ import annotations

import json
from decimal import Decimal

import pytest

from ai.backend.common.events.event_types.kernel.types import (
    KernelCreationInfo,
    ServicePortInfo,
    UsedDevice,
    UsedDevices,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    BinarySize,
    ContainerId,
    DeviceId,
    DeviceModelInfo,
    DeviceName,
    ResourceSlotEntry,
    ServicePortProtocols,
    SlotName,
)


def _device(
    used: dict[str, Decimal],
    *,
    model_name: str | None = None,
    processing_units: int | None = None,
    memory_size: int | None = None,
) -> UsedDevice:
    return UsedDevice(
        model_name=model_name,
        used={ResourceSlotName(slot): amount for slot, amount in used.items()},
        processing_units=processing_units,
        memory_size=memory_size,
    )


def _info_with(
    used_devices: UsedDevices,
    service_ports: list[ServicePortInfo] | None = None,
) -> KernelCreationInfo:
    return KernelCreationInfo(
        container_id=ContainerId("c0ffee"),
        kernel_host="127.0.0.1",
        repl_in_port=2000,
        repl_out_port=2001,
        service_ports=service_ports if service_ports is not None else [],
        used_devices=used_devices,
    )


@pytest.fixture
def creation_info() -> KernelCreationInfo:
    """A kernel holding one cpu core, 1 GiB, and half of one GPU."""
    return _info_with(
        UsedDevices(
            units={
                DeviceName("cpu"): {DeviceId("0"): _device({"cpu": Decimal("1")})},
                DeviceName("mem"): {DeviceId("root"): _device({"mem": Decimal("1073741824")})},
                DeviceName("cuda"): {
                    DeviceId("0"): _device(
                        {"cuda.device": Decimal("1"), "cuda.shares": Decimal("0.5")},
                        model_name="A100",
                        processing_units=54,
                        memory_size=21474836480,
                    )
                },
            }
        ),
        service_ports=[
            ServicePortInfo(
                name="jupyter",
                protocol=ServicePortProtocols.HTTP,
                container_ports=[8080],
                host_ports=[30000],
                is_inference=False,
            )
        ],
    )


class TestKernelCreationInfo:
    """The whole payload has to survive JSON, since that is how it reaches the manager."""

    def test_roundtrip_keeps_every_typed_leaf(self, creation_info: KernelCreationInfo) -> None:
        restored = KernelCreationInfo.model_validate_json(creation_info.model_dump_json())

        assert restored == creation_info
        assert restored.service_ports[0].protocol is ServicePortProtocols.HTTP
        cuda = restored.used_devices.units[DeviceName("cuda")][DeviceId("0")]
        assert cuda.model_name == "A100"
        assert (cuda.processing_units, cuda.memory_size) == (54, 21474836480)
        assert cuda.used[ResourceSlotName("cuda.shares")] == Decimal("0.5")

    def test_one_unit_is_described_once(self, creation_info: KernelCreationInfo) -> None:
        """The unit metered along two axes appears once, with both amounts under it —
        which is what merging the attached devices into the usage buys."""
        cuda = creation_info.used_devices.units[DeviceName("cuda")]

        assert list(cuda) == [DeviceId("0")]
        assert set(cuda[DeviceId("0")].used) == {"cuda.device", "cuda.shares"}

    def test_an_intrinsic_device_reports_neither_unit(
        self, creation_info: KernelCreationInfo
    ) -> None:
        """Only an accelerator measures itself; the cpu and mem plugins report nothing."""
        cpu = creation_info.used_devices.units[DeviceName("cpu")][DeviceId("0")]

        assert (cpu.model_name, cpu.processing_units, cpu.memory_size) == (None, None, None)

    def test_derived_totals_are_not_written_to_the_wire(
        self, creation_info: KernelCreationInfo
    ) -> None:
        """The allocations are the payload; the per-slot sum is derived and stays off it."""
        assert "slot_totals" not in creation_info.model_dump_json()


class TestSlotTotals:
    """`slot_totals` is what a caller records as the kernel's usage."""

    def test_amounts_are_summed_across_units(self) -> None:
        used = UsedDevices(
            units={
                DeviceName("cuda"): {
                    DeviceId("0"): _device({"cuda.shares": Decimal("0.5")}),
                    DeviceId("1"): _device({"cuda.shares": Decimal("0.25")}),
                }
            }
        )

        totals = {e.resource_type: e.quantity for e in used.slot_totals}

        assert totals == {"cuda.shares": "0.75"}

    def test_a_unit_reports_each_of_its_slots(self, creation_info: KernelCreationInfo) -> None:
        totals = {e.resource_type: e.quantity for e in creation_info.used_devices.slot_totals}

        assert totals == {
            "cpu": "1",
            "mem": "1073741824",
            "cuda.device": "1",
            "cuda.shares": "0.5",
        }

    @pytest.mark.parametrize(
        ("slot", "amount"),
        [
            ("mem", Decimal("4294967296")),
            ("mem", Decimal("1073741825")),
            ("cuda.shares", Decimal("0.5")),
        ],
        ids=["exact_bytes", "off_by_one_byte", "fractional"],
    )
    def test_amounts_survive_the_wire_exactly(self, slot: str, amount: Decimal) -> None:
        info = _info_with(
            UsedDevices(units={DeviceName(slot): {DeviceId("0"): _device({slot: amount})}})
        )

        restored = KernelCreationInfo.model_validate_json(info.model_dump_json())

        assert restored.used_devices.slot_totals == [
            ResourceSlotEntry(resource_type=ResourceSlotName(slot), quantity=str(amount))
        ]

    @pytest.mark.parametrize("amount", ["Infinity", "-Infinity", "NaN"], ids=str)
    def test_non_finite_amount_is_rejected(self, amount: str) -> None:
        """A unit supplies a finite share of what it has; an unbounded amount is a
        limit, which is not what this carries."""
        payload = json.dumps({
            "units": {
                "cpu": {
                    "0": {
                        "model_name": None,
                        "used": {"cpu": amount},
                        "processing_units": None,
                        "memory_size": None,
                    }
                }
            }
        })

        with pytest.raises(BackendAISchemaValidationFailed):
            UsedDevices.model_validate_json(payload)

    def test_a_kernel_holding_nothing_totals_nothing(self) -> None:
        assert UsedDevices(units={}).slot_totals == []


class TestFromAllocations:
    """`from_allocations()` is where the agent's two views of a kernel's devices meet."""

    ALLOCATIONS = {
        DeviceName("cpu"): {SlotName("cpu"): {DeviceId("0"): Decimal(2)}},
        DeviceName("cuda"): {
            SlotName("cuda.device"): {DeviceId("0"): Decimal(1)},
            SlotName("cuda.shares"): {DeviceId("0"): Decimal("0.5")},
        },
    }

    def test_a_unit_metered_on_two_axes_is_described_once(self) -> None:
        """The spec keys amounts by slot and then by unit; the payload keys them the
        other way round, so the unit on two axes has to collapse into one entry."""
        cuda = UsedDevices.from_allocations(self.ALLOCATIONS, {}).units[DeviceName("cuda")]

        assert list(cuda) == [DeviceId("0")]
        assert cuda[DeviceId("0")].used == {
            "cuda.device": Decimal(1),
            "cuda.shares": Decimal("0.5"),
        }

    def test_the_reported_device_facts_are_joined_by_device_id(self) -> None:
        attached: dict[DeviceName, list[DeviceModelInfo]] = {
            DeviceName("cuda"): [
                {
                    "device_id": DeviceId("0"),
                    "model_name": "A100",
                    "data": {"mem": BinarySize(21474836480), "proc": 54},
                }
            ]
        }

        cuda = UsedDevices.from_allocations(self.ALLOCATIONS, attached).units[DeviceName("cuda")]

        assert (
            cuda[DeviceId("0")].model_name,
            cuda[DeviceId("0")].processing_units,
            cuda[DeviceId("0")].memory_size,
        ) == ("A100", 54, 21474836480)

    def test_an_intrinsic_device_reports_no_model(self) -> None:
        """A cpu or mem plugin attaches nothing, so its units carry the amounts alone."""
        cpu = UsedDevices.from_allocations(self.ALLOCATIONS, {DeviceName("cpu"): []}).units[
            DeviceName("cpu")
        ][DeviceId("0")]

        assert (cpu.model_name, cpu.processing_units, cpu.memory_size) == (None, None, None)
        assert cpu.used == {"cpu": Decimal(2)}

    def test_the_totals_are_what_the_manager_records_as_occupancy(self) -> None:
        totals = {
            entry.resource_type: entry.quantity
            for entry in UsedDevices.from_allocations(self.ALLOCATIONS, {}).slot_totals
        }

        assert totals == {"cpu": "2", "cuda.device": "1", "cuda.shares": "0.5"}
