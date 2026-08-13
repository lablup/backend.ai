from __future__ import annotations

import uuid
from decimal import Decimal
from pathlib import Path

import pytest

from ai.backend.common.data.kernel.types import (
    AttachedDeviceData,
    DeviceCapacityData,
    KernelCreationInfo,
    KernelResourceSpecData,
    MountData,
    ServicePortData,
)
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    ContainerId,
    DeviceId,
    DeviceName,
    KernelId,
    MountPermission,
    MountTypes,
    ResourceSlotEntry,
    ServicePortProtocols,
    SlotName,
)


@pytest.fixture
def creation_info() -> KernelCreationInfo:
    return KernelCreationInfo(
        id=KernelId(uuid.uuid4()),
        container_id=ContainerId("c0ffee"),
        kernel_host="127.0.0.1",
        repl_in_port=2000,
        repl_out_port=2001,
        stdin_port=0,
        stdout_port=0,
        resource_group=ResourceGroupName("default"),
        agent_addr="tcp://127.0.0.1:6011",
        service_ports=[
            ServicePortData(
                name="jupyter",
                protocol=ServicePortProtocols.HTTP,
                container_ports=[8080],
                host_ports=[30000],
            )
        ],
        resource_spec=KernelResourceSpecData(
            slots=[
                ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity="2"),
                ResourceSlotEntry(resource_type=ResourceSlotName("mem"), quantity="4294967296"),
            ],
            allocations={
                DeviceName("cpu"): {ResourceSlotName("cpu"): {DeviceId("root"): Decimal("2")}},
                DeviceName("mem"): {
                    ResourceSlotName("mem"): {DeviceId("root"): Decimal("4294967296")}
                },
            },
            mounts=[
                MountData(
                    type=MountTypes.BIND,
                    source=Path("/host/a"),
                    target=Path("/home/work/a"),
                    permission=MountPermission.READ_WRITE,
                )
            ],
        ),
        attached_devices={
            DeviceName("cuda"): [
                AttachedDeviceData(
                    device_id=DeviceId("0"),
                    model_name="A100",
                    data=DeviceCapacityData(mem=1024, proc=8),
                )
            ]
        },
    )


class TestKernelCreationInfo:
    """The whole payload has to survive JSON, since that is how it reaches the manager."""

    def test_roundtrip_keeps_every_typed_leaf(self, creation_info: KernelCreationInfo) -> None:
        restored = KernelCreationInfo.model_validate_json(creation_info.model_dump_json())

        assert restored == creation_info
        assert restored.resource_spec.mounts[0].target == Path("/home/work/a")
        assert restored.resource_spec.mounts[0].permission is MountPermission.READ_WRITE
        assert restored.service_ports[0].protocol is ServicePortProtocols.HTTP
        assert restored.attached_devices[DeviceName("cuda")][0].data.mem == 1024


class TestMountData:
    def test_every_field_is_required(self) -> None:
        """No defaults: a producer states what it mounted rather than inheriting one."""
        for omitted in ("type", "source", "permission"):
            kwargs = {
                "type": MountTypes.BIND,
                "source": Path("/host/a"),
                "target": Path("/home/work/a"),
                "permission": MountPermission.READ_ONLY,
            }
            del kwargs[omitted]
            with pytest.raises(Exception):
                MountData(**kwargs)  # type: ignore[arg-type]

    def test_source_may_be_absent_but_must_be_stated(self) -> None:
        mount = MountData(
            type=MountTypes.BIND,
            source=None,
            target=Path("/home/work/a"),
            permission=MountPermission.READ_ONLY,
        )

        assert mount.source is None


class TestResourceSlotAggregation:
    """`to_resource_slot()` is what a caller records as the kernel's occupancy."""

    def test_amounts_are_summed_across_devices(self) -> None:
        spec = KernelResourceSpecData(
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

        slots = spec.to_resource_slot()

        assert slots[SlotName("cpu")] == Decimal("4")
        assert slots[SlotName("cuda.shares")] == Decimal("0.75")

    @pytest.mark.parametrize(
        ("device", "slot", "amount"),
        [
            ("mem", "mem", Decimal("4294967296")),
            ("mem", "mem", Decimal("1073741825")),
            ("cuda", "cuda.shares", Decimal("0.5")),
            ("cpu", "cpu", Decimal("Infinity")),
        ],
        ids=["exact_bytes", "off_by_one_byte", "fractional", "unbounded"],
    )
    def test_amounts_survive_the_wire_exactly(
        self, device: str, slot: str, amount: Decimal
    ) -> None:
        """`Infinity` is here because the default `Decimal` constraint rejects it.

        A fractional amount belongs to a share slot: `ResourceSlot` rejects fractional
        bytes outright.
        """
        spec = KernelResourceSpecData(
            allocations={DeviceName(device): {ResourceSlotName(slot): {DeviceId("0"): amount}}}
        )

        restored = KernelResourceSpecData.model_validate_json(spec.model_dump_json())

        assert restored.allocations[DeviceName(device)][ResourceSlotName(slot)] == {
            DeviceId("0"): amount
        }
        assert restored.to_resource_slot()[SlotName(slot)] == amount

    def test_slot_without_any_device_allocation_is_omitted(self) -> None:
        """Omitted, not zero — the caller stores the result as occupancy, where a slot
        present at zero and a slot absent are not the same statement."""
        spec = KernelResourceSpecData(
            allocations={DeviceName("cuda"): {ResourceSlotName("cuda.device"): {}}}
        )

        assert dict(spec.to_resource_slot()) == {}
