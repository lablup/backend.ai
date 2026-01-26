from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Mapping
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import BinarySize, DeviceId, SessionId, SlotName
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}

    async def get(self, key: str) -> Any:
        return None


@pytest.fixture
async def registry_ctx() -> AsyncGenerator[
    tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, ManagerConfigProvider, MagicMock, MagicMock
    ],
    None,
]:
    mocked_etcd = DummyEtcd()
    mock_etcd_config_loader = MagicMock()
    mock_etcd_config_loader.update_resource_slots = AsyncMock()
    mock_etcd_config_loader._etcd = mocked_etcd

    mock_loader = MagicMock()
    mock_loader.load = AsyncMock(
        return_value={
            "db": {"name": "test_db", "user": "postgres", "password": "develove"},
            "logging": {},
        }
    )
    mock_config_provider = await ManagerConfigProvider.create(
        loader=mock_loader,
        etcd_watcher=MagicMock(),
        legacy_etcd_config_loader=mock_etcd_config_loader,
    )
    mock_db = MagicMock()
    mock_dbconn = MagicMock()
    mock_dbsess = MagicMock()
    mock_dbconn_ctx = MagicMock()
    mock_dbsess_ctx = MagicMock()
    mock_dbresult = MagicMock()
    mock_dbresult.rowcount = 1
    mock_agent_cache = MagicMock()
    mock_db.connect = MagicMock(return_value=mock_dbconn_ctx)
    mock_db.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_db.begin_session = MagicMock(return_value=mock_dbsess_ctx)
    mock_dbconn_ctx.__aenter__ = AsyncMock(return_value=mock_dbconn)
    mock_dbconn_ctx.__aexit__ = AsyncMock()
    mock_dbsess_ctx.__aenter__ = AsyncMock(return_value=mock_dbsess)
    mock_dbsess_ctx.__aexit__ = AsyncMock()
    mock_dbconn.execute = AsyncMock(return_value=mock_dbresult)
    mock_dbconn.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_dbsess.execute = AsyncMock(return_value=mock_dbresult)
    mock_dbsess.begin_session = AsyncMock(return_value=mock_dbsess_ctx)
    mock_valkey_stat_client = MagicMock()
    mock_redis_live = MagicMock()
    mock_redis_live.hset = AsyncMock()
    mock_redis_image = AsyncMock()
    mock_redis_image.close = AsyncMock()
    mock_redis_image.get_all_agents_images = AsyncMock(return_value=[])
    mock_redis_image.get_agent_images = AsyncMock(return_value=[])
    mock_redis_image.add_agent_image = AsyncMock()
    mock_redis_image.remove_agent_image = AsyncMock()
    mock_redis_image.remove_agent = AsyncMock()
    mock_redis_image.clear_all_images = AsyncMock()
    mock_event_dispatcher = MagicMock()
    mock_event_producer = MagicMock()
    mock_event_producer.anycast_event = AsyncMock()
    mock_event_producer.broadcast_event = AsyncMock()
    mock_event_producer.anycast_and_broadcast_event = AsyncMock()

    mock_event_hub = MagicMock()
    mock_event_hub.publish = AsyncMock()
    mock_event_hub.subscribe = AsyncMock()
    mock_event_hub.unsubscribe = AsyncMock()

    hook_plugin_ctx = HookPluginContext(mocked_etcd, {})  # type: ignore
    network_plugin_ctx = NetworkPluginContext(mocked_etcd, {})  # type: ignore

    mock_scheduling_controller = AsyncMock()
    mock_scheduling_controller.enqueue_session = AsyncMock(return_value=SessionId(uuid.uuid4()))
    mock_scheduling_controller.dispatch_session_events = AsyncMock()

    mock_agent_client_pool = MagicMock()

    registry = AgentRegistry(
        config_provider=mock_config_provider,
        db=mock_db,
        agent_cache=mock_agent_cache,
        agent_client_pool=mock_agent_client_pool,
        valkey_stat=mock_valkey_stat_client,
        valkey_live=mock_redis_live,
        valkey_image=mock_redis_image,
        event_producer=mock_event_producer,
        event_hub=mock_event_hub,
        storage_manager=None,  # type: ignore
        hook_plugin_ctx=hook_plugin_ctx,
        network_plugin_ctx=network_plugin_ctx,
        scheduling_controller=mock_scheduling_controller,  # type: ignore
        manager_public_key=PublicKey(b"GqK]ZYY#h*9jAQbGxSwkeZX3Y*%b+DiY$7ju6sh{"),
        manager_secret_key=SecretKey(b"37KX6]ac^&hcnSaVo=-%eVO9M]ENe8v=BOWF(Sw$"),
    )
    await registry.init()
    try:
        yield (
            registry,
            mock_dbconn,
            mock_dbsess,
            mock_dbresult,
            mock_config_provider,
            mock_event_dispatcher,
            mock_event_producer,
        )
    finally:
        await registry.shutdown()


@pytest.mark.asyncio
async def test_convert_resource_spec_to_resource_slot(
    registry_ctx: tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, ManagerConfigProvider, MagicMock, MagicMock
    ],
) -> None:
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
    assert converted_allocations["cuda.shares"] == Decimal("4.5")
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
    assert converted_allocations["cpu"] == Decimal("4")
    assert converted_allocations["ram"] == Decimal(BinarySize.from_str("1g")) * 3
