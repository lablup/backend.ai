from __future__ import annotations

import zlib
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

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
    mock_get_known_container_registries = AsyncMock(
        # Hint: [{"project": {"registry_name": "url"}, ...}]
        return_value=[
            {
                "": {"index.docker.io": "https://registry-1.docker.io"},
            }
        ]
    )
    mocker.patch(
        "ai.backend.manager.models.container_registry.ContainerRegistryRow.get_known_container_registries",
        mock_get_known_container_registries,
    )

    def mocked_entrypoints(entry_point_group: str, blocklist: Optional[set[str]] = None):
        return []

    mocker.patch("ai.backend.common.plugin.scan_entrypoints", mocked_entrypoints)

    registry, mock_dbconn, mock_dbsess, mock_dbresult, mock_config_provider, _, _ = registry_ctx

    # Mock redis_live methods since redis_helper is no longer used
    mock_redis_live = MagicMock()
    mock_redis_live.update_agent_last_seen = AsyncMock()
    mocker.patch.object(registry, "valkey_live", mock_redis_live)
    image_data = zlib.compress(
        msgpack.packb([
            ("index.docker.io/lablup/python:3.6-ubuntu18.04",),
        ])
    )

    _1 = Decimal("1")
    _4 = Decimal("4")
    _1g = Decimal("1073741824")
    _2g = Decimal("2147483648")

    # Join - mock repository to return a new agent join
    mock_dbresult.first = MagicMock(return_value=None)
    registry.repositories.agent_registry.repository.handle_agent_heartbeat.return_value = (  # type: ignore
        True,  # instance_rejoin = True for new agent
        None,  # row = None for new agent
        True,  # should_update_cache = True
    )

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
    mock_config_provider.legacy_etcd_config_loader.update_resource_slots.assert_awaited_once()
    # Verify repository method was called with correct parameters
    registry.repositories.agent_registry.repository.handle_agent_heartbeat.assert_called_once()  # type: ignore

    # Update alive instance
    mock_config_provider.legacy_etcd_config_loader.update_resource_slots.reset_mock()
    registry.repositories.agent_registry.repository.handle_agent_heartbeat.reset_mock()  # type: ignore
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
    # Mock repository to return an existing agent update
    registry.repositories.agent_registry.repository.handle_agent_heartbeat.return_value = (  # type: ignore
        False,  # instance_rejoin = False for existing agent
        mock_dbresult.first.return_value,  # row = existing agent data
        True,  # should_update_cache = True
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
    mock_config_provider.legacy_etcd_config_loader.update_resource_slots.assert_awaited_once()
    # Verify repository method was called
    registry.repositories.agent_registry.repository.handle_agent_heartbeat.assert_called_once()  # type: ignore

    # Rejoin
    mock_config_provider.legacy_etcd_config_loader.update_resource_slots.reset_mock()
    registry.repositories.agent_registry.repository.handle_agent_heartbeat.reset_mock()  # type: ignore
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
    # Mock repository to return a rejoining agent
    registry.repositories.agent_registry.repository.handle_agent_heartbeat.return_value = (  # type: ignore
        True,  # instance_rejoin = True for rejoining agent
        mock_dbresult.first.return_value,  # row = existing agent data with LOST status
        True,  # should_update_cache = True
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
    mock_config_provider.legacy_etcd_config_loader.update_resource_slots.assert_awaited_once()
    # Verify repository method was called
    registry.repositories.agent_registry.repository.handle_agent_heartbeat.assert_called_once()  # type: ignore


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
