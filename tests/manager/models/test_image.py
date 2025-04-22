import asyncio

import pytest
import sqlalchemy as sa
from aiohttp import web
from aioresponses import aioresponses
from graphene import Schema
from graphene.test import Client

from ai.backend.common.events.bgtask import (
    BgtaskCancelledEvent,
    BgtaskDoneEvent,
    BgtaskFailedEvent,
)
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
)
from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.common.types import AgentId
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.server import (
    agent_registry_ctx,
    background_task_ctx,
    database_ctx,
    distributed_lock_ctx,
    event_dispatcher_plugin_ctx,
    event_hub_ctx,
    event_producer_ctx,
    hook_plugin_ctx,
    idle_checker_ctx,
    message_queue_ctx,
    monitoring_ctx,
    network_plugin_ctx,
    processors_ctx,
    redis_ctx,
    services_ctx,
    storage_manager_ctx,
)
from ai.backend.testutils.mock import mock_aioresponses_sequential_payloads, setup_dockerhub_mocking


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Queries, mutation=Mutations, auto_camelcase=False))


def get_graphquery_context(
    background_task_manager,
    services_ctx,
    processor_ctx,
    database_engine: ExtendedAsyncSAEngine,
) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        config_provider=None,  # type: ignore
        etcd=MagicMock(),  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=database_engine,  # type: ignore
        redis_stat=None,  # type: ignore
        redis_image=None,  # type: ignore
        redis_live=None,  # type: ignore
        manager_status=None,  # type: ignore
        known_slot_types=None,  # type: ignore
        background_task_manager=background_task_manager,  # type: ignore
        storage_manager=None,  # type: ignore
        registry=None,  # type: ignore
        idle_checker_host=None,  # type: ignore
        network_plugin_ctx=None,  # type: ignore
        services_ctx=services_ctx,  # type: ignore
        metric_observer=GraphQLMetricObserver.instance(),
        processors=processor_ctx,
    )


FIXTURES_DOCKER_REGISTRIES = [
    {
        "container_registries": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "url": "http://mock_registry",
                "type": "docker",
                "project": "lablup",
                "registry_name": "mock_registry",
            },
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "url": "http://mock_registry",
                "type": "docker",
                "project": "other",
                "registry_name": "mock_registry",
            },
        ]
    }
]


@pytest.mark.asyncio
@pytest.mark.timeout(60)
@pytest.mark.parametrize("extra_fixtures", FIXTURES_DOCKER_REGISTRIES)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "project": None,
            "mock_dockerhub_responses": {
                "get_token": {"token": "fake-token"},
                "get_catalog": {
                    "repositories": [
                        "lablup/python",
                        "other/dangling-image1",
                        "other/dangling-image2",
                        "other/python",
                    ]
                },
                "get_tags": mock_aioresponses_sequential_payloads([
                    {"tags": ["latest"]},
                    {"tags": []},  # dangling image should be skipped
                    {"tags": None},  # dangling image should be skipped
                    {"tags": ["latest"]},
                ]),
                "get_manifest": {
                    "schemaVersion": 2,
                    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "config": {
                        "mediaType": "application/vnd.docker.container.image.v1+json",
                        "size": 100,
                        "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                    },
                    "layers": [],
                },
                "get_config": {
                    "architecture": "amd64",
                    "os": "linux",
                },
            },
            "expected_result": {
                "images": {("lablup/python", "latest"), ("other/python", "latest")},
            },
        },
        {
            "project": "lablup",
            "mock_dockerhub_responses": {
                "get_token": {"token": "fake-token"},
                "get_catalog": {"repositories": ["lablup/python", "other/python"]},
                "get_tags": {"tags": ["latest"]},
                "get_manifest": {
                    "schemaVersion": 2,
                    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "config": {
                        "mediaType": "application/vnd.docker.container.image.v1+json",
                        "size": 100,
                        "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                    },
                    "layers": [],
                },
                "get_config": {
                    "architecture": "amd64",
                    "os": "linux",
                },
            },
            "expected_result": {
                "images": {("lablup/python", "latest")},
            },
        },
    ],
    ids=[
        "Rescan images for all projects",
        "Rescan images for a specific project",
    ],
)
async def test_image_rescan_on_docker_registry(
    client: Client,
    test_case,
    etcd_fixture,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    extra_fixtures,
    database_fixture,
    event_dispatcher_test_ctx,
    create_app_and_client,
):
    app, _ = await create_app_and_client(
        [
            event_hub_ctx,
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            redis_ctx,
            message_queue_ctx,
            event_producer_ctx,
            storage_manager_ctx,
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
            distributed_lock_ctx,
            idle_checker_ctx,
            processors_ctx,
        ],
        [".events", ".auth"],
    )
    root_ctx: RootContext = app["_root.context"]
    dispatcher: EventDispatcher = root_ctx.event_dispatcher
    done_handler_ctx = {}
    done_event = asyncio.Event()

    async def done_sub(
        context: web.Application,
        source: AgentId,
        event: BgtaskDoneEvent,
    ) -> None:
        done_handler_ctx["event_name"] = event.event_name()
        update_body = asdict(event)
        done_handler_ctx.update(**update_body)
        done_event.set()

    async def fail_sub(
        context: web.Application,
        source: AgentId,
        event: BgtaskFailedEvent,
    ) -> None:
        assert False, "Background task failed"

    async def cancel_sub(
        context: web.Application,
        source: AgentId,
        event: BgtaskCancelledEvent,
    ) -> None:
        assert False, "Background task was cancelled"

    dispatcher.subscribe(BgtaskDoneEvent, app, done_sub)
    dispatcher.subscribe(BgtaskFailedEvent, app, fail_sub)
    dispatcher.subscribe(BgtaskCancelledEvent, app, cancel_sub)

    mock_dockerhub_responses = test_case["mock_dockerhub_responses"]

    with aioresponses() as mocked:
        registry_url = extra_fixtures["container_registries"][0]["url"]
        setup_dockerhub_mocking(mocked, registry_url, mock_dockerhub_responses)

        context = get_graphquery_context(
            root_ctx.background_task_manager,
            root_ctx.services_ctx,
            root_ctx.processors,
            root_ctx.db,
        )
        image_rescan_query = """
            mutation ($registry: String, $project: String) {
                rescan_images(registry: $registry, project: $project) {
                    ok
                    msg
                    task_id
                }
            }
        """
        variables = {
            "registry": "mock_registry",
            "project": test_case["project"],
        }

        res = await client.execute_async(image_rescan_query, context=context, variables=variables)
        assert res["data"]["rescan_images"]["ok"]

        await done_event.wait()
        # Even if the response value is ok: true, the rescan background task might have failed.
        # So we need to separately verify whether the actual task was successful.
        assert str(done_handler_ctx["task_id"]) == res["data"]["rescan_images"]["task_id"]

        async with root_ctx.db.begin_readonly_session() as db_session:
            res = await db_session.execute(sa.select(ImageRow.image, ImageRow.tag))
            populated_img_names = res.fetchall()
            assert set(populated_img_names) == test_case["expected_result"]["images"]


@pytest.mark.rescan_cr_backend_ai
@pytest.mark.timeout(60)
async def test_image_rescan_on_cr_backend_ai(
    client: Client,
    etcd_fixture,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    event_dispatcher_test_ctx,
    create_app_and_client,
):
    app, _ = await create_app_and_client(
        [
            event_hub_ctx,
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            redis_ctx,
            message_queue_ctx,
            event_producer_ctx,
            storage_manager_ctx,
            monitoring_ctx,
            network_plugin_ctx,
            hook_plugin_ctx,
            agent_registry_ctx,
            event_dispatcher_test_ctx,
            services_ctx,
            network_plugin_ctx,
            storage_manager_ctx,
            agent_registry_ctx,
            background_task_ctx,
            distributed_lock_ctx,
            idle_checker_ctx,
            processors_ctx,
        ],
        [".events", ".auth"],
    )
    root_ctx: RootContext = app["_root.context"]
    dispatcher: EventDispatcher = root_ctx.event_dispatcher
    done_handler_ctx = {}
    done_event = asyncio.Event()

    async def done_sub(
        context: web.Application,
        source: AgentId,
        event: BgtaskDoneEvent,
    ) -> None:
        done_handler_ctx["event_name"] = event.event_name()
        update_body = asdict(event)
        done_handler_ctx.update(**update_body)
        done_event.set()

    async def fail_sub(
        context: web.Application,
        source: AgentId,
        event: BgtaskFailedEvent,
    ) -> None:
        assert False, "Background task failed"

    async def cancel_sub(
        context: web.Application,
        source: AgentId,
        event: BgtaskCancelledEvent,
    ) -> None:
        assert False, "Background task was cancelled"

    dispatcher.subscribe(BgtaskDoneEvent, app, done_sub)
    dispatcher.subscribe(BgtaskFailedEvent, app, fail_sub)
    dispatcher.subscribe(BgtaskCancelledEvent, app, cancel_sub)

    context = get_graphquery_context(
        root_ctx.background_task_manager,
        root_ctx.services_ctx,
        root_ctx.processors,
        root_ctx.db,
    )
    image_rescan_query = """
        mutation ($registry: String, $project: String) {
            rescan_images(registry: $registry, project: $project) {
                ok
                msg
                task_id
            }
        }
    """
    variables = {
        "registry": "cr.backend.ai",
        "project": "stable",
    }

    res = await client.execute_async(image_rescan_query, context=context, variables=variables)
    assert res["data"]["rescan_images"]["ok"]
    await done_event.wait()
    errors = done_handler_ctx.get("errors", None)
    assert not errors, f"Rescan task failed with errors: {errors}"
