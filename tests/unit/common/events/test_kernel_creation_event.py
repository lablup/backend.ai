from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.events.event_types.kernel.anycast import (
    KernelPreparingAnycastEvent,
    KernelStartedAnycastEvent,
)
from ai.backend.common.events.event_types.kernel.types import (
    KernelCreationInfo,
    ServicePortInfo,
    UsedDevice,
    UsedDevices,
)
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    ContainerId,
    DeviceId,
    DeviceName,
    KernelId,
    ServicePortProtocols,
    SessionId,
)


@pytest.fixture
def kernel_id() -> KernelId:
    return KernelId(uuid.uuid4())


@pytest.fixture
def session_id() -> SessionId:
    return SessionId(uuid.uuid4())


@pytest.fixture
def creation_info() -> KernelCreationInfo:
    return KernelCreationInfo(
        container_id=ContainerId("c0ffee"),
        kernel_host="127.0.0.1",
        repl_in_port=2000,
        repl_out_port=2001,
        service_ports=[
            ServicePortInfo(
                name="jupyter",
                protocol=ServicePortProtocols.HTTP,
                container_ports=[8080],
                host_ports=[30000],
                is_inference=False,
            )
        ],
        used_devices=UsedDevices(
            units={
                DeviceName("mem"): {
                    DeviceId("0"): UsedDevice(
                        model_name=None,
                        used={ResourceSlotName("mem"): Decimal(4 * 1024**3)},
                        processing_units=None,
                        memory_size=None,
                    )
                },
                DeviceName("cuda"): {
                    DeviceId("0"): UsedDevice(
                        model_name="A100",
                        used={ResourceSlotName("cuda.shares"): Decimal("0.5")},
                        processing_units=54,
                        memory_size=21474836480,
                    )
                },
            }
        ),
    )


class TestKernelCreationEventPayload:
    """`creation_info` must survive the JSON wire body unchanged.

    It is the one event field that used to travel as pickled `ResourceSlot` /
    `Decimal` values, so it is where a lossy conversion would show up first.
    `TestKernelCreationInfo` covers the type on its own; what is at stake here is
    that carrying it as an event field does not flatten it on the way.
    """

    def test_creation_info_roundtrip(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        creation_info: KernelCreationInfo,
    ) -> None:
        event = KernelStartedAnycastEvent(
            kernel_id=kernel_id, session_id=session_id, creation_info=creation_info
        )

        restored = KernelStartedAnycastEvent.from_message(event.to_message())

        assert restored == event
        assert restored.creation_info.service_ports[0].protocol is ServicePortProtocols.HTTP
        cuda = restored.creation_info.used_devices.units[DeviceName("cuda")][DeviceId("0")]
        assert cuda.used[ResourceSlotName("cuda.shares")] == Decimal("0.5")
        assert cuda.memory_size == 21474836480

    def test_earlier_creation_events_carry_no_creation_info(
        self, kernel_id: KernelId, session_id: SessionId
    ) -> None:
        event = KernelPreparingAnycastEvent(kernel_id=kernel_id, session_id=session_id)

        assert "creation_info" not in event.to_message().payload
        assert KernelPreparingAnycastEvent.from_message(event.to_message()) == event
