import uuid

import pytest
from graphene import Schema
from graphene.test import Client

from ai.backend.manager.models.gql import GraphQueryContext, Mutations, Queries
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VirtualFolder
from ai.backend.manager.server import (
    database_ctx,
)


@pytest.fixture(scope="module")
def client() -> Client:
    return Client(Schema(query=Queries, mutation=Mutations, auto_camelcase=False))


def get_graphquery_context(database_engine: ExtendedAsyncSAEngine) -> GraphQueryContext:
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
        background_task_manager=None,  # type: ignore
        storage_manager=None,  # type: ignore
        registry=None,  # type: ignore
        idle_checker_host=None,  # type: ignore
    )


FIXTURES_VFOLDERS = [
    {
        "users": [
            {
                "uuid": "00000000-0000-0000-0000-000000000000",
                "username": "admin",
                "email": "admin@lablup.com",
                "password": "wJalrXUt",
                "need_password_change": False,
                "full_name": "Admin Lablup",
                "description": "Lablup's Admin Account",
                "status": "active",
                "status_info": "admin-requested",
                "domain_name": "mock_domain",
                "resource_policy": "default",
                "role": "superadmin",
            }
        ],
        "vfolders": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "host": "mock",
                "domain_name": "mock_domain",
                "name": "mock_vfolder_1",
                "quota_scope_id": "user:00000000-0000-0000-0000-000000000000",
                "usage_mode": "general",
                "permission": "rw",
                "ownership_type": "user",
                "status": "ready",
                "cloneable": False,
                "max_files": 1000,
                "num_files": 100,
                "user": "00000000-0000-0000-0000-000000000000",
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "host": "mock",
                "domain_name": "mock_domain",
                "name": "mock_vfolder_2",
                "quota_scope_id": "user:00000000-0000-0000-0000-000000000000",
                "usage_mode": "general",
                "permission": "rw",
                "ownership_type": "user",
                "status": "ready",
                "cloneable": False,
                "max_files": 1000,
                "num_files": 100,
                "user": "00000000-0000-0000-0000-000000000000",
            },
        ],
    }
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_fixtures",
    FIXTURES_VFOLDERS,
)
async def test_batch_load_by_id(
    database_fixture,
    create_app_and_client,
):
    mock_user = uuid.UUID("00000000-0000-0000-0000-000000000000")
    mock_vfolders = [
        uuid.UUID("00000000-0000-0000-0000-000000000001"),
        uuid.UUID("00000000-0000-0000-0000-000000000002"),
    ]

    test_app, _ = await create_app_and_client(
        [
            database_ctx,
        ],
        [],
    )

    root_ctx = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db)

    result = await VirtualFolder.batch_load_by_id(
        context,
        mock_vfolders[:1],
    )
    assert len(result) == 1
    assert result[0].id == mock_vfolders[0]

    result = await VirtualFolder.batch_load_by_id(
        context,
        mock_vfolders[:2],
    )
    assert len(result) == 2
    assert result[0].id == mock_vfolders[0]
    assert result[1].id == mock_vfolders[1]

    result = await VirtualFolder.batch_load_by_id(
        context,
        mock_vfolders[:1],
        user_id=mock_user,
    )
    assert len(result) == 1
    assert result[0].id == mock_vfolders[0]

    result = await VirtualFolder.batch_load_by_id(
        context,
        mock_vfolders[:1],
        user_id=mock_user,
        domain_name="mock_domain",
    )
    assert len(result) == 1
    assert result[0].id == mock_vfolders[0]

    result = await VirtualFolder.batch_load_by_id(
        context,
        mock_vfolders[:1],
        user_id=mock_user,
        domain_name="INVALID",
    )
    assert len(result) == 1
    assert result[0] is None
