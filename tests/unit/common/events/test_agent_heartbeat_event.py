from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.events.event_types.agent.anycast import AgentHeartbeatEvent
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import DeviceName, ResourceSlotEntry, SlotName, SlotTypes


class TestAgentHeartbeatEvent:
    """`slot_key_and_units` keys survive the round trip whichever form they arrive in.

    `AgentInfo.normalize_slot_keys` accepts both plain strings and `SlotName`, so these
    cases pin that down: the key form a caller happens to use must not change the event
    the manager ends up holding.
    """

    @pytest.mark.parametrize(
        ("agent_info_dict", "expected_slot_keys"),
        [
            (
                {
                    "ip": "192.168.1.100",
                    "region": "us-west-2",
                    "scaling_group": "default",
                    "addr": "tcp://192.168.1.100:6001",
                    "public_key": None,
                    "public_host": "agent-1.example.com",
                    "available_resource_slots": [
                        ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity="4"),
                        ResourceSlotEntry(resource_type=ResourceSlotName("mem"), quantity="8192"),
                    ],
                    "slot_key_and_units": {
                        "cpu": SlotTypes.COUNT,
                        "mem": SlotTypes.BYTES,
                    },  # String keys
                    "version": "25.3.0",
                    "compute_plugins": {
                        DeviceName("cpu"): {"version": "1.0.0"},
                    },
                    "images": b"",
                    "architecture": "x86_64",
                    "auto_terminate_abusing_kernel": False,
                    "images_opts": {"compression": "zlib"},
                },
                {
                    SlotName("cpu"): SlotTypes.COUNT,
                    SlotName("mem"): SlotTypes.BYTES,
                },
            ),
            (
                {
                    "ip": "192.168.1.100",
                    "region": "us-west-2",
                    "scaling_group": "default",
                    "addr": "tcp://192.168.1.100:6001",
                    "public_key": None,
                    "public_host": "agent-1.example.com",
                    "available_resource_slots": [
                        ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity="4"),
                        ResourceSlotEntry(resource_type=ResourceSlotName("mem"), quantity="8192"),
                    ],
                    "slot_key_and_units": {
                        SlotName("cpu"): SlotTypes.COUNT,
                        SlotName("mem"): SlotTypes.BYTES,
                    },  # SlotName keys
                    "version": "25.3.0",
                    "compute_plugins": {
                        DeviceName("cpu"): {"version": "1.0.0"},
                    },
                    "images": b"",
                    "architecture": "x86_64",
                    "auto_terminate_abusing_kernel": False,
                    "images_opts": {"compression": "zlib"},
                },
                {
                    SlotName("cpu"): SlotTypes.COUNT,
                    SlotName("mem"): SlotTypes.BYTES,
                },
            ),
            (
                {
                    "ip": "192.168.1.100",
                    "region": "us-west-2",
                    "scaling_group": "default",
                    "addr": "tcp://192.168.1.100:6001",
                    "public_key": None,
                    "public_host": "agent-1.example.com",
                    "available_resource_slots": [
                        ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity="4"),
                        ResourceSlotEntry(resource_type=ResourceSlotName("mem"), quantity="8192"),
                        ResourceSlotEntry(
                            resource_type=ResourceSlotName("cuda.device"), quantity="2"
                        ),
                    ],
                    "slot_key_and_units": {
                        "cpu": SlotTypes.COUNT,  # String key
                        SlotName("mem"): SlotTypes.BYTES,  # SlotName key
                        "cuda.device": SlotTypes.COUNT,  # String key with device type
                    },
                    "version": "25.3.0",
                    "compute_plugins": {
                        DeviceName("cpu"): {"version": "1.0.0"},
                    },
                    "images": b"",
                    "architecture": "x86_64",
                    "auto_terminate_abusing_kernel": False,
                    "images_opts": {"compression": "zlib"},
                },
                {
                    SlotName("cpu"): SlotTypes.COUNT,
                    SlotName("mem"): SlotTypes.BYTES,
                    SlotName("cuda.device"): SlotTypes.COUNT,
                },
            ),
        ],
        ids=["string_keys", "slotname_keys", "mixed_keys"],
    )
    async def test_serialization_deserialization_round_trip_with_different_key_formats(
        self,
        agent_info_dict: dict[str, Any],
        expected_slot_keys: dict[SlotName, SlotTypes],
    ) -> None:
        """The slot key form used to build the event does not survive into a difference."""
        event = AgentHeartbeatEvent(agent_info=AgentInfo.model_validate(agent_info_dict))

        serialized = event.serialize()
        deserialized = AgentHeartbeatEvent.deserialize(serialized)

        assert deserialized.agent_info.slot_key_and_units == expected_slot_keys
