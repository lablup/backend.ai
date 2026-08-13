from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

import pytest

from ai.backend.common.events.event_types.kernel.types import (
    AttachedDevice,
    DeviceCapacity,
    DeviceOccupancy,
    KernelCreationInfo,
    KernelOccupancy,
    ServicePortInfo,
    SlotOccupancy,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    ContainerId,
    DeviceId,
    DeviceName,
    ResourceSlotEntry,
    ServicePortProtocols,
)


def _info_with(**overrides: object) -> KernelCreationInfo:
    fields: dict[str, object] = {
        "container_id": ContainerId("c0ffee"),
        "kernel_host": "127.0.0.1",
        "repl_in_port": 2000,
        "repl_out_port": 2001,
        "service_ports": [],
        "attached_devices": {},
        "occupancy": KernelOccupancy(devices={}),
        **overrides,
    }
    return KernelCreationInfo(**fields)  # type: ignore[arg-type]


def _occupancy(**per_slot: dict[str, Decimal]) -> KernelOccupancy:
    """Build an occupancy, taking the device name from the slot name as the agent does."""
    by_device: defaultdict[DeviceName, dict[ResourceSlotName, SlotOccupancy]] = defaultdict(dict)
    for slot, amounts in per_slot.items():
        by_device[DeviceName(slot.partition(".")[0])][ResourceSlotName(slot)] = SlotOccupancy(
            amounts={DeviceId(device_id): amount for device_id, amount in amounts.items()}
        )
    return KernelOccupancy(
        devices={name: DeviceOccupancy(slots=slots) for name, slots in by_device.items()}
    )


@pytest.fixture
def creation_info() -> KernelCreationInfo:
    return _info_with(
        service_ports=[
            ServicePortInfo(
                name="jupyter",
                protocol=ServicePortProtocols.HTTP,
                container_ports=[8080],
                host_ports=[30000],
                is_inference=False,
            )
        ],
        attached_devices={
            DeviceName("cuda"): [
                AttachedDevice(
                    device_id=DeviceId("0"),
                    model_name="A100",
                    data=DeviceCapacity(mem=1024, proc=8),
                )
            ]
        },
        occupancy=_occupancy(cpu={"0": Decimal("2")}, mem={"root": Decimal("4294967296")}),
    )


class TestKernelCreationInfo:
    """The whole payload has to survive JSON, since that is how it reaches the manager."""

    def test_roundtrip_keeps_every_typed_leaf(self, creation_info: KernelCreationInfo) -> None:
        restored = KernelCreationInfo.model_validate_json(creation_info.model_dump_json())

        assert restored == creation_info
        assert restored.service_ports[0].protocol is ServicePortProtocols.HTTP
        assert restored.attached_devices[DeviceName("cuda")][0].data.mem == 1024
        assert restored.occupancy.devices[DeviceName("mem")].slots[
            ResourceSlotName("mem")
        ].amounts == {DeviceId("root"): Decimal("4294967296")}

    def test_derived_totals_are_not_written_to_the_wire(
        self, creation_info: KernelCreationInfo
    ) -> None:
        """The occupancy is the payload; the per-slot sum is derived and stays off it."""
        assert "slot_totals" not in creation_info.model_dump_json()


class TestSlotTotals:
    """`slot_totals` is what a caller records as the kernel's occupancy."""

    def test_one_device_supplying_several_slots(self) -> None:
        """`cuda` is metered along two axes at once, by the same two units."""
        occupancy = KernelOccupancy(
            devices={
                DeviceName("cuda"): DeviceOccupancy(
                    slots={
                        ResourceSlotName("cuda.shares"): SlotOccupancy(
                            amounts={
                                DeviceId("0"): Decimal("0.5"),
                                DeviceId("1"): Decimal("0.25"),
                            }
                        ),
                        ResourceSlotName("cuda.device"): SlotOccupancy(
                            amounts={DeviceId("0"): Decimal("1"), DeviceId("1"): Decimal("1")}
                        ),
                    }
                )
            }
        )

        totals = {e.resource_type: e.quantity for e in occupancy.slot_totals}

        assert totals == {"cuda.shares": "0.75", "cuda.device": "2"}

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
        info = _info_with(occupancy=_occupancy(**{slot: {"0": amount}}))

        restored = KernelCreationInfo.model_validate_json(info.model_dump_json())

        assert restored.occupancy.slot_totals == [
            ResourceSlotEntry(resource_type=ResourceSlotName(slot), quantity=str(amount))
        ]

    @pytest.mark.parametrize("amount", ["Infinity", "-Infinity", "NaN"], ids=str)
    def test_non_finite_amount_is_rejected(self, amount: str) -> None:
        """A device supplies a finite share of what it has; an unbounded amount is a
        limit, which is not what this carries."""
        payload = (
            '{"devices":{"cpu":{"slots":{"cpu":{"amounts":{"0":"%s"}}}}}}' % amount  # noqa: UP031
        )

        with pytest.raises(BackendAISchemaValidationFailed):
            KernelOccupancy.model_validate_json(payload)

    def test_slot_supplied_by_no_device_is_omitted(self) -> None:
        """Omitted, not zero — the caller stores the result as occupancy, where a slot
        present at zero and a slot absent are not the same statement."""
        occupancy = KernelOccupancy(
            devices={
                DeviceName("cuda"): DeviceOccupancy(
                    slots={ResourceSlotName("cuda.device"): SlotOccupancy(amounts={})}
                )
            }
        )

        assert occupancy.slot_totals == []
