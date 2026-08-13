from __future__ import annotations

from decimal import Decimal

import pytest

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.interchange.kernel import (
    AttachedDeviceData,
    DeviceCapacityData,
    KernelCreationInfo,
    ServicePortData,
)
from ai.backend.common.types import (
    ContainerId,
    DeviceId,
    DeviceName,
    ResourceSlotEntry,
    ServicePortProtocols,
)


@pytest.fixture
def creation_info() -> KernelCreationInfo:
    return KernelCreationInfo(
        container_id=ContainerId("c0ffee"),
        kernel_host="127.0.0.1",
        repl_in_port=2000,
        repl_out_port=2001,
        service_ports=[
            ServicePortData(
                name="jupyter",
                protocol=ServicePortProtocols.HTTP,
                container_ports=[8080],
                host_ports=[30000],
            )
        ],
        attached_devices={
            DeviceName("cuda"): [
                AttachedDeviceData(
                    device_id=DeviceId("0"),
                    model_name="A100",
                    data=DeviceCapacityData(mem=1024, proc=8),
                )
            ]
        },
        allocations={
            DeviceName("cpu"): {ResourceSlotName("cpu"): {DeviceId("root"): Decimal("2")}},
            DeviceName("mem"): {ResourceSlotName("mem"): {DeviceId("root"): Decimal("4294967296")}},
        },
    )


class TestKernelCreationInfo:
    """The whole payload has to survive JSON, since that is how it reaches the manager."""

    def test_roundtrip_keeps_every_typed_leaf(self, creation_info: KernelCreationInfo) -> None:
        restored = KernelCreationInfo.model_validate_json(creation_info.model_dump_json())

        assert restored == creation_info
        assert restored.service_ports[0].protocol is ServicePortProtocols.HTTP
        assert restored.attached_devices[DeviceName("cuda")][0].data.mem == 1024
        assert restored.allocations[DeviceName("mem")][ResourceSlotName("mem")] == {
            DeviceId("root"): Decimal("4294967296")
        }


class TestResourceSlotEntries:
    """`to_resource_slot_entries()` is what a caller records as the kernel's occupancy."""

    def test_amounts_are_summed_across_devices(self) -> None:
        info = _info_with(
            allocations={
                DeviceName("cpu"): {
                    ResourceSlotName("cpu"): {
                        DeviceId("0"): Decimal("2"),
                        DeviceId("1"): Decimal("2"),
                    }
                },
                DeviceName("cuda"): {
                    ResourceSlotName("cuda.shares"): {
                        DeviceId("0"): Decimal("0.5"),
                        DeviceId("1"): Decimal("0.25"),
                    }
                },
            }
        )

        entries = {e.resource_type: e.quantity for e in info.to_resource_slot_entries()}

        assert entries == {"cpu": "4", "cuda.shares": "0.75"}

    @pytest.mark.parametrize(
        ("slot", "amount"),
        [
            ("mem", Decimal("4294967296")),
            ("mem", Decimal("1073741825")),
            ("cuda.shares", Decimal("0.5")),
            ("cpu", Decimal("Infinity")),
        ],
        ids=["exact_bytes", "off_by_one_byte", "fractional", "unbounded"],
    )
    def test_amounts_survive_the_wire_exactly(self, slot: str, amount: Decimal) -> None:
        """`Infinity` is here because the default `Decimal` constraint rejects it."""
        info = _info_with(
            allocations={
                DeviceName(slot): {ResourceSlotName(slot): {DeviceId("0"): amount}},
            }
        )

        restored = KernelCreationInfo.model_validate_json(info.model_dump_json())

        assert restored.allocations[DeviceName(slot)][ResourceSlotName(slot)] == {
            DeviceId("0"): amount
        }
        assert restored.to_resource_slot_entries() == [
            ResourceSlotEntry(resource_type=ResourceSlotName(slot), quantity=str(amount))
        ]

    def test_slot_without_any_device_allocation_is_omitted(self) -> None:
        """Omitted, not zero — the caller stores the result as occupancy, where a slot
        present at zero and a slot absent are not the same statement."""
        info = _info_with(allocations={DeviceName("cuda"): {ResourceSlotName("cuda.device"): {}}})

        assert info.to_resource_slot_entries() == []


def _info_with(**overrides: object) -> KernelCreationInfo:
    return KernelCreationInfo(
        container_id=ContainerId("c0ffee"),
        kernel_host="127.0.0.1",
        repl_in_port=2000,
        repl_out_port=2001,
        **overrides,  # type: ignore[arg-type]
    )
