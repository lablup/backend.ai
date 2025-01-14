import uuid

import pytest

from ai.backend.manager.models.gql import GraphQueryContext
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VirtualFolder
from ai.backend.manager.server import (
    database_ctx,
)


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


FIXTURES = [
    {
        "users": [
            {
                "uuid": "00000000-0000-0000-0000-000000000000",
                "username": "mock_user",
                "email": "",
                "password": "",
                "need_password_change": False,
                "full_name": "",
                "description": "",
                "status": "active",
                "status_info": "admin-requested",
                "domain_name": "default",
                "resource_policy": "default",
                "role": "superadmin",
            }
        ],
        "groups": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "mock_group",
                "description": "",
                "is_active": True,
                "domain_name": "default",
                "resource_policy": "default",
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
            },
        ],
        "vfolders": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "host": "mock",
                "name": "mock_vfolder_1",
                "quota_scope_id": "user:00000000-0000-0000-0000-000000000000",
                "usage_mode": "general",
                "permission": "rw",
                "ownership_type": "user",
                "status": "ready",
                "cloneable": False,
                "max_files": 0,
                "num_files": 0,
                "user": "00000000-0000-0000-0000-000000000000",
                "group": None,
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "host": "mock",
                "name": "mock_vfolder_2",
                "quota_scope_id": "user:00000000-0000-0000-0000-000000000000",
                "usage_mode": "general",
                "permission": "rw",
                "ownership_type": "user",
                "status": "ready",
                "cloneable": False,
                "max_files": 0,
                "num_files": 0,
                "user": "00000000-0000-0000-0000-000000000000",
                "group": None,
            },
            {
                "id": "00000000-0000-0000-0000-000000000003",
                "host": "mock",
                "name": "mock_vfolder_3",
                "quota_scope_id": "project:00000000-0000-0000-0000-000000000000",
                "usage_mode": "general",
                "permission": "rw",
                "ownership_type": "group",
                "status": "ready",
                "cloneable": False,
                "max_files": 0,
                "num_files": 0,
                "user": None,
                "group": "00000000-0000-0000-0000-000000000000",
            },
        ],
    }
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_fixtures",
    FIXTURES,
)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "vfolder_ids": [uuid.UUID("00000000-0000-0000-0000-000000000001")],
            "user_id": None,
            "group_id": None,
            "expected_result": [uuid.UUID("00000000-0000-0000-0000-000000000001")],
        },
        {
            "vfolder_ids": [
                uuid.UUID("00000000-0000-0000-0000-000000000001"),
                uuid.UUID("00000000-0000-0000-0000-000000000002"),
            ],
            "user_id": None,
            "group_id": None,
            "expected_result": [
                uuid.UUID("00000000-0000-0000-0000-000000000001"),
                uuid.UUID("00000000-0000-0000-0000-000000000002"),
            ],
        },
        {
            "vfolder_ids": [uuid.UUID("00000000-0000-0000-0000-000000000001")],
            "user_id": uuid.UUID("00000000-0000-0000-0000-000000000000"),
            "group_id": None,
            "expected_result": [uuid.UUID("00000000-0000-0000-0000-000000000001")],
        },
    ],
    ids=[
        "Batchload a vfolder by id",
        "Batchload multiple vfolders by ids",
        "Batchload a vfolder by user_id",
    ],
)
async def test_batch_load_by_id(
    test_case,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            database_ctx,
        ],
        [],
    )

    root_ctx = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db)

    vfolder_ids = test_case["vfolder_ids"]
    user_id = test_case["user_id"]
    group_id = test_case["group_id"]
    expected_result = test_case["expected_result"]

    result = await VirtualFolder.batch_load_by_id(
        context,
        vfolder_ids,
        user_id=user_id,
        group_id=group_id,
    )

    assert len(result) == len(expected_result)
    for res, expected_id in zip(result, expected_result):
        if expected_id is None:
            assert res is None
        else:
            assert res.id == expected_id
