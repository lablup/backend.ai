from __future__ import annotations

import zlib
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.sql.dml import Insert, Update

from ai.backend.common import msgpack
from ai.backend.common.types import BinarySize, DeviceId, ResourceSlot, SlotName
from ai.backend.manager.defs import DEFAULT_IMAGE_ARCH
from ai.backend.manager.models import AgentStatus
from ai.backend.manager.registry import AgentRegistry


@pytest.mark.asyncio
async def test_handle_heartbeat(
    registry_ctx: tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock
    ],
    mocker,
) -> None:
    mock_get_known_registries = AsyncMock(
        return_value=[
            {"index.docker.io": "https://registry-1.docker.io"},
        ]
    )
    mocker.patch("ai.backend.manager.registry.get_known_registries", mock_get_known_registries)
    mock_redis_wrapper = MagicMock()
    mock_redis_wrapper.execute = AsyncMock()
    mocker.patch("ai.backend.manager.registry.redis_helper", mock_redis_wrapper)

    def mocked_entrypoints(entry_point_group: str, blocklist: set[str] = None):
        return []

    mocker.patch("ai.backend.common.plugin.scan_entrypoints", mocked_entrypoints)

    registry, mock_dbconn, mock_dbsess, mock_dbresult, mock_shared_config, _, _ = registry_ctx
    image_data = zlib.compress(
        msgpack.packb([
            ("index.docker.io/lablup/python:3.6-ubuntu18.04",),
        ])
    )

    _1 = Decimal("1")
    _4 = Decimal("4")
    _1g = Decimal("1073741824")
    _2g = Decimal("2147483648")

    # Join
    mock_dbresult.first = MagicMock(return_value=None)
    await registry.handle_heartbeat(
        "i-001",
        {
            "scaling_group": "sg-testing",
            "resource_slots": {"cpu": ("count", _1), "mem": ("bytes", _1g)},
            "region": "ap-northeast-2",
            "addr": "10.0.0.5",
            "public_host": "10.0.0.5",
            "public_key": None,
            "architecture": DEFAULT_IMAGE_ARCH,
            "version": "19.12.0",
            "compute_plugins": [],
            "images": image_data,
            "auto_terminate_abusing_kernel": False,
        },
    )
    mock_shared_config.update_resource_slots.assert_awaited_once()
    q = mock_dbconn.execute.await_args_list[1].args[0]
    assert isinstance(q, Insert)

    # Update alive instance
    mock_shared_config.update_resource_slots.reset_mock()
    mock_dbconn.execute.reset_mock()
    mock_dbresult.first = MagicMock(
        return_value={
            "status": AgentStatus.ALIVE,
            "addr": "10.0.0.5",
            "public_host": "10.0.0.5",
            "public_key": None,
            "architecture": DEFAULT_IMAGE_ARCH,
            "scaling_group": "sg-testing",
            "available_slots": ResourceSlot({"cpu": _1, "mem": _1g}),
            "version": "19.12.0",
            "compute_plugins": [],
            "auto_terminate_abusing_kernel": False,
        }
    )
    await registry.handle_heartbeat(
        "i-001",
        {
            "scaling_group": "sg-testing",
            "resource_slots": {"cpu": ("count", _1), "mem": ("bytes", _2g)},
            "region": "ap-northeast-2",
            "addr": "10.0.0.6",
            "public_host": "10.0.0.5",
            "public_key": None,
            "architecture": DEFAULT_IMAGE_ARCH,
            "version": "19.12.0",
            "compute_plugins": [],
            "images": image_data,
            "auto_terminate_abusing_kernel": False,
        },
    )
    mock_shared_config.update_resource_slots.assert_awaited_once()
    q = mock_dbconn.execute.await_args_list[1].args[0]
    assert isinstance(q, Update)
    q_params = q.compile().params
    assert q_params["addr"] == "10.0.0.6"
    assert q_params["available_slots"] == ResourceSlot({"cpu": _1, "mem": _2g})
    assert "scaling_group" not in q_params

    # Rejoin
    mock_shared_config.update_resource_slots.reset_mock()
    mock_dbconn.execute.reset_mock()
    mock_dbresult.first = MagicMock(
        return_value={
            "status": AgentStatus.LOST,
            "addr": "10.0.0.5",
            "public_host": "10.0.0.5",
            "public_key": None,
            "architecture": DEFAULT_IMAGE_ARCH,
            "scaling_group": "sg-testing",
            "available_slots": ResourceSlot({"cpu": _1, "mem": _1g}),
            "version": "19.12.0",
            "compute_plugins": [],
            "auto_terminate_abusing_kernel": False,
        }
    )
    await registry.handle_heartbeat(
        "i-001",
        {
            "scaling_group": "sg-testing2",
            "resource_slots": {"cpu": ("count", _4), "mem": ("bytes", _2g)},
            "region": "ap-northeast-2",
            "addr": "10.0.0.6",
            "public_host": "10.0.0.5",
            "public_key": None,
            "architecture": DEFAULT_IMAGE_ARCH,
            "version": "19.12.0",
            "compute_plugins": [],
            "images": image_data,
            "auto_terminate_abusing_kernel": False,
        },
    )
    mock_shared_config.update_resource_slots.assert_awaited_once()
    q = mock_dbconn.execute.await_args_list[1].args[0]
    assert isinstance(q, Update)
    q_params = q.compile().params
    assert q_params["status"] == AgentStatus.ALIVE
    assert q_params["addr"] == "10.0.0.6"
    assert "lost_at=NULL" in str(q)  # stringified and removed from bind params
    assert q_params["available_slots"] == ResourceSlot({"cpu": _4, "mem": _2g})
    assert q_params["scaling_group"] == "sg-testing2"
    assert "compute_plugins" in q_params
    assert "version" in q_params


@pytest.mark.asyncio
async def test_convert_resource_spec_to_resource_slot(
    registry_ctx: tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock
    ],
):
    registry, _, _, _, _, _, _ = registry_ctx
    allocations = {
        "cuda": {
            SlotName("cuda.shares"): {
                DeviceId("a0"): "2.5",
                DeviceId("a1"): "2.0",
            },
        },
    }
    converted_allocations = registry.convert_resource_spec_to_resource_slot(allocations)
    assert converted_allocations["cuda.shares"] == "4.5"
    allocations = {
        "cpu": {
            SlotName("cpu"): {
                DeviceId("a0"): "3",
                DeviceId("a1"): "1",
            },
        },
        "ram": {
            SlotName("ram"): {
                DeviceId("b0"): "2.5g",
                DeviceId("b1"): "512m",
            },
        },
    }
    converted_allocations = registry.convert_resource_spec_to_resource_slot(allocations)
    assert converted_allocations["cpu"] == "4"
    assert converted_allocations["ram"] == str(Decimal(BinarySize.from_str("1g")) * 3)
