import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import attr
import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.common import redis_helper
from ai.backend.common.events import BgtaskDoneEvent, BgtaskUpdatedEvent, EventDispatcher
from ai.backend.common.types import AgentId
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.server import (
    background_task_ctx,
    database_ctx,
    event_dispatcher_ctx,
    hook_plugin_ctx,
    mock_agent_registry_ctx,
    monitoring_ctx,
    network_plugin_ctx,
    redis_ctx,
    shared_config_ctx,
    storage_manager_ctx,
)


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Queries, mutation=Mutations, auto_camelcase=False))


def get_graphquery_context(root_context: RootContext) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        local_config=None,  # type: ignore
        shared_config=None,  # type: ignore
        etcd=None,  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=root_context.db,  # type: ignore
        redis_stat=None,  # type: ignore
        redis_image=None,  # type: ignore
        redis_live=None,  # type: ignore
        manager_status=None,  # type: ignore
        known_slot_types=None,  # type: ignore
        background_task_manager=root_context.background_task_manager,  # type: ignore
        storage_manager=None,  # type: ignore
        registry=root_context.registry,  # type: ignore
        idle_checker_host=None,  # type: ignore
        network_plugin_ctx=None,  # type: ignore
    )


def agent_template(id: str, status: AgentStatus):
    return {
        "id": id,
        "status": status.name,
        "scaling_group": "default",
        "schedulable": True,
        "region": "local",
        "available_slots": {},
        "occupied_slots": {},
        "addr": "tcp://127.0.0.1:6011",
        "public_host": "127.0.0.1",
        "version": "24.12.0a1",
        "architecture": "x86_64",
        "compute_plugins": {},
    }


FIXTURES = [
    {
        "agents": [
            agent_template("i-ag1", AgentStatus.ALIVE),
            agent_template("i-ag2", AgentStatus.ALIVE),
            agent_template("i-ag3", AgentStatus.LOST),
        ]
    }
]


@patch("ai.backend.manager.registry.AgentRegistry.scan_gpu_alloc_map", new_callable=AsyncMock)
@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES)
async def test_scan_gpu_alloc_maps(
    mock_agent_rpc: MagicMock,
    client,
    local_config,
    etcd_fixture,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            shared_config_ctx,
            database_ctx,
            redis_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            event_dispatcher_ctx,
            storage_manager_ctx,
            network_plugin_ctx,
            mock_agent_registry_ctx,
            background_task_ctx,
        ],
        [".auth"],
    )

    root_ctx: RootContext = test_app["_root.context"]
    dispatcher: EventDispatcher = root_ctx.event_dispatcher
    done_handler_ctx: dict = {}
    update_handler_ctx = {"call_count": 0}
    done_event = asyncio.Event()

    async def update_sub(
        context: None,
        source: AgentId,
        event: BgtaskUpdatedEvent,
    ) -> None:
        update_handler_ctx["call_count"] += 1
        update_body = attr.asdict(event)  # type: ignore
        update_handler_ctx.update(**update_body)

    async def done_sub(
        context: None,
        source: AgentId,
        event: BgtaskDoneEvent,
    ) -> None:
        update_body = attr.asdict(event)  # type: ignore
        done_handler_ctx.update(**update_body)
        done_event.set()

    dispatcher.subscribe(BgtaskUpdatedEvent, None, update_sub)
    dispatcher.subscribe(BgtaskDoneEvent, None, done_sub)

    mock_agent_rpc.side_effect = [
        {"00000000-0000-0000-0000-000000000001": "10.00"},
        {"00000000-0000-0000-0000-000000000002": "5.00"},
    ]

    context = get_graphquery_context(root_ctx)
    query = """
        mutation {
            scan_gpu_alloc_maps {
                ok
                msg
                task_id
            }
        }
        """

    res = await client.execute_async(query, variables={}, context_value=context)
    assert res["data"]["scan_gpu_alloc_maps"]["ok"]
    await done_event.wait()

    assert str(done_handler_ctx["task_id"]) == res["data"]["scan_gpu_alloc_maps"]["task_id"]
    # 2 update events and 1 done event
    assert update_handler_ctx["call_count"] == 3

    stats = await redis_helper.execute(
        root_ctx.redis_stat,
        lambda r: r.mget("gpu_alloc_map.i-ag1", "gpu_alloc_map.i-ag2", "gpu_alloc_map.i-ag3"),
    )

    expected = [
        b'{"00000000-0000-0000-0000-000000000001": "10.00"}',
        b'{"00000000-0000-0000-0000-000000000002": "5.00"}',
        None,
    ]
    assert stats == expected
