import json
from typing import Any

import pytest


def _device(npu: int, bus_id: str) -> dict[str, Any]:
    return {
        "group_id": "0",
        "npu": npu,
        "name": "RBLN-CR13",
        "sid": f"{npu:016d}",
        "uuid": f"00000000-0000-0000-0000-{npu:012d}",
        "device": f"rbln{npu}",
        "status": "normal",
        "fw_ver": "3.5.1",
        "pci": {
            "dev": "0x2130",
            "bus_id": bus_id,
            "numa_node": "0",
            "link_speed": "32.0GT/s",
            "link_width": "16",
        },
        "temperature": "34C",
        "card_power": "100372000uW",
        "pstate": "P10",
        "memory": {"used": "0", "total": "150323855360"},
        "util": "0.0",
        "board_info": "00000009",
        "location": 0,
    }


@pytest.fixture
def stat_payload() -> dict[str, Any]:
    """`rbln-smi -g -j` output of an idle 4-card node."""
    bus_ids = ["0000:f3:00.0", "0000:f4:00.0", "0000:fd:00.0", "0000:fe:00.0"]
    return {
        "KMD_version": "3.5.1",
        "devices": [_device(npu, bus_id) for npu, bus_id in enumerate(bus_ids)],
        "contexts": [],
    }


@pytest.fixture
def stat_json(stat_payload: dict[str, Any]) -> str:
    return json.dumps(stat_payload)
