import asyncio
import json

import attr
import pytest
import sqlalchemy as sa
from aiohttp import web
from aioresponses import aioresponses
from graphene import Schema
from graphene.test import Client

from ai.backend.common.events import BgtaskDoneEvent, EventDispatcher
from ai.backend.common.types import AgentId
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.server import (
    background_task_ctx,
    database_ctx,
    event_dispatcher_ctx,
    hook_plugin_ctx,
    monitoring_ctx,
    redis_ctx,
    shared_config_ctx,
)


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Queries, mutation=Mutations, auto_camelcase=False))


def get_graphquery_context(
    background_task_manager, database_engine: ExtendedAsyncSAEngine
) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        local_config=None,  # type: ignore
        shared_config=None,  # type: ignore
        etcd=None,  # type: ignore
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
    )


FIXTURES_REGISTRIES = [
    {
        "container_registries": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "url": "http://mock_registry",
                "type": "docker",
                "project": "lablup",
                "registry_name": "mock_registry",
            }
        ]
    }
]


@pytest.mark.asyncio
@pytest.mark.timeout(60)
@pytest.mark.parametrize("extra_fixtures", FIXTURES_REGISTRIES)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "mock_dockerhub_responses": {
                "get_token": {"token": "fake-token"},
                "get_catalog": {"repositories": ["lablup/python"]},
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
            }
        }
    ],
)
async def test_image_rescan(
    test_case,
    client: Client,
    etcd_fixture,
    extra_fixtures,
    database_fixture,
    create_app_and_client,
):
    app, _ = await create_app_and_client(
        [
            shared_config_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
        ],
        [".events", ".auth"],
    )
    root_ctx: RootContext = app["_root.context"]
    dispatcher: EventDispatcher = root_ctx.event_dispatcher
    done_handler_ctx = {}

    async def done_sub(
        context: web.Application,
        source: AgentId,
        event: BgtaskDoneEvent,
    ) -> None:
        done_handler_ctx["event_name"] = event.name
        update_body = attr.asdict(event)  # type: ignore
        done_handler_ctx.update(**update_body)

    dispatcher.subscribe(BgtaskDoneEvent, app, done_sub)

    mock_dockerhub_responses = test_case["mock_dockerhub_responses"]

    def setup_mocks(mocked):
        registry_base = "http://mock_registry"

        # /v2/ endpoint
        mocked.get(
            f"{registry_base}/v2/",
            status=200,
            payload=mock_dockerhub_responses["get_tags"],
            repeat=True,
        )

        # catalog
        mocked.get(
            f"{registry_base}/v2/_catalog?n=30",
            status=200,
            payload=mock_dockerhub_responses["get_catalog"],
        )

        # tags
        mocked.get(
            f"{registry_base}/v2/lablup/python/tags/list?n=10",
            status=200,
            payload=mock_dockerhub_responses["get_tags"],
        )

        # manifest
        mocked.get(
            f"{registry_base}/v2/lablup/python/manifests/latest",
            status=200,
            payload=mock_dockerhub_responses["get_manifest"],
            headers={
                "Content-Type": "application/vnd.docker.distribution.manifest.v2+json",
            },
        )

        config_data = mock_dockerhub_responses["get_manifest"]["config"]
        image_digest = config_data["digest"]

        # config blob(JSON)
        mocked.get(
            f"{registry_base}/v2/lablup/python/blobs/{image_digest}",
            status=200,
            body=json.dumps(mock_dockerhub_responses["get_config"]).encode("utf-8"),
            payload=mock_dockerhub_responses["get_config"],
            repeat=True,
        )

    with aioresponses() as mocked:
        setup_mocks(mocked)

        context = get_graphquery_context(root_ctx.background_task_manager, root_ctx.db)
        image_rescan_query = """
            mutation ($registry: String!) {
                rescan_images(registry: $registry) {
                    ok
                    msg
                    task_id
                }
            }
        """
        variables = {
            "registry": "mock_registry",
        }

        res = await client.execute_async(image_rescan_query, context=context, variables=variables)
        await asyncio.sleep(2)

        assert res["data"]["rescan_images"]["ok"]
        assert str(done_handler_ctx["task_id"]) == res["data"]["rescan_images"]["task_id"]

        async with root_ctx.db.begin_readonly_session() as db_session:
            target_registry_id = extra_fixtures["container_registries"][0]["id"]
            res = await db_session.execute(
                sa.select(sa.exists().where(ImageRow.registry_id == target_registry_id))
            )
            image_row_populated = res.scalar()
            assert image_row_populated
