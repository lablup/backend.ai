import asyncio
import json
from dataclasses import asdict
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.event_types.bgtask.broadcast import BgtaskDoneEvent
from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.common.types import AgentId
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.models.gql import GraphQueryContext, Mutation, Query
from ai.backend.manager.server import (
    agent_registry_ctx,
    background_task_ctx,
    database_ctx,
    event_dispatcher_plugin_ctx,
    event_hub_ctx,
    event_producer_ctx,
    hook_plugin_ctx,
    message_queue_ctx,
    monitoring_ctx,
    network_plugin_ctx,
    redis_ctx,
    repositories_ctx,
    services_ctx,
    storage_manager_ctx,
)


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))


def get_graphquery_context(root_context: RootContext) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        config_provider=None,  # type: ignore
        etcd=None,  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=root_context.db,  # type: ignore
        valkey_stat=None,  # type: ignore
        valkey_image=None,  # type: ignore
        valkey_live=None,  # type: ignore
        valkey_schedule=None,  # type: ignore
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
        scheduler_repository=None,  # type: ignore
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
    mock_etcd_ctx,
    mock_config_provider_ctx,
    client,
    bootstrap_config,
    etcd_fixture,
    database_fixture,
    event_dispatcher_test_ctx,
    create_app_and_client,
    test_case,
    extra_fixtures,
) -> None:
    test_app, _ = await create_app_and_client(
        [
            event_hub_ctx,
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            redis_ctx,
            message_queue_ctx,
            event_producer_ctx,
            storage_manager_ctx,
            repositories_ctx,
            monitoring_ctx,
            network_plugin_ctx,
            hook_plugin_ctx,
            event_dispatcher_plugin_ctx,
            agent_registry_ctx,
            event_dispatcher_test_ctx,
            services_ctx,
            network_plugin_ctx,
            storage_manager_ctx,
            agent_registry_ctx,
            background_task_ctx,
        ],
        [],
    )

    root_ctx: RootContext = test_app["_root.context"]
    dispatcher: EventDispatcher = root_ctx.event_dispatcher
    done_handler_ctx: dict[str, Any] = {}
    done_event = asyncio.Event()

    async def done_sub(
        context: None,
        source: AgentId,
        event: BgtaskDoneEvent,
    ) -> None:
        update_body = asdict(event)
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
    raw_alloc_map_cache = await root_ctx.valkey_stat._client.client.mget(["gpu_alloc_map.i-ag1"])
    alloc_map_cache = [
        json.loads(stat) if stat is not None else None for stat in raw_alloc_map_cache
    ]
    assert alloc_map_cache == test_case["expected"]["redis"]
