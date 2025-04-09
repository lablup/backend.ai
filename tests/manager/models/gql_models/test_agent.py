import asyncio
import json
from unittest.mock import AsyncMock, patch

import attr
import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.common import redis_helper
from ai.backend.common.events import BgtaskDoneEvent, EventDispatcher
from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.common.types import AgentId
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.server import (
    agent_registry_ctx,
    background_task_ctx,
    database_ctx,
    event_dispatcher_ctx,
    hook_plugin_ctx,
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
        services_ctx=None,  # type: ignore
        metric_observer=GraphQLMetricObserver.instance(),
        processors=None,  # type: ignore
    )


EXTRA_FIXTURES = {
    "agents": [
        {
            "id": "i-ag1",
            "status": AgentStatus.ALIVE.name,
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
    ]
}


@patch("ai.backend.manager.registry.AgentRegistry.scan_gpu_alloc_map", new_callable=AsyncMock)
@pytest.mark.asyncio
@pytest.mark.timeout(60)
@pytest.mark.parametrize(
    "test_case, extra_fixtures",
    [
        (
            {
                "mock_agent_responses": [
                    {
                        "00000000-0000-0000-0000-000000000001": "10.00",
                        "00000000-0000-0000-0000-000000000002": "5.00",
                    },
                ],
                "expected": {
                    "redis": [
                        {
                            "00000000-0000-0000-0000-000000000001": "10.00",
                            "00000000-0000-0000-0000-000000000002": "5.00",
                        },
                    ],
                },
            },
            EXTRA_FIXTURES,
        ),
    ],
)
async def test_scan_gpu_alloc_maps(
    mock_agent_responses,
    client,
    local_config,
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    test_case,
    extra_fixtures,
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
            agent_registry_ctx,
            background_task_ctx,
        ],
        [],
    )

    root_ctx: RootContext = test_app["_root.context"]
    dispatcher: EventDispatcher = root_ctx.event_dispatcher
    done_handler_ctx = {}
    done_event = asyncio.Event()

    async def done_sub(
        context: None,
        source: AgentId,
        event: BgtaskDoneEvent,
    ) -> None:
        update_body = attr.asdict(event)  # type: ignore
        done_handler_ctx.update(**update_body)
        done_event.set()

    dispatcher.subscribe(BgtaskDoneEvent, None, done_sub)

    mock_agent_responses.side_effect = test_case["mock_agent_responses"]

    context = get_graphquery_context(root_ctx)
    query = """
        mutation ($agent_id: String!) {
            rescan_gpu_alloc_maps (agent_id: $agent_id) {
                task_id
            }
        }
        """

    res = await client.execute_async(
        query,
        context_value=context,
        variables={
            "agent_id": "i-ag1",
        },
    )

    await done_event.wait()

    assert str(done_handler_ctx["task_id"]) == res["data"]["rescan_gpu_alloc_maps"]["task_id"]
    alloc_map_keys = [f"gpu_alloc_map.{agent['id']}" for agent in extra_fixtures["agents"]]
    raw_alloc_map_cache = await redis_helper.execute(
        root_ctx.redis_stat,
        lambda r: r.mget(*alloc_map_keys),
    )
    alloc_map_cache = [
        json.loads(stat) if stat is not None else None for stat in raw_alloc_map_cache
    ]
    assert alloc_map_cache == test_case["expected"]["redis"]
