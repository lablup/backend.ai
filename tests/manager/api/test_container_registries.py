import json

import pytest

from ai.backend.manager.server import (
    database_ctx,
    hook_plugin_ctx,
    monitoring_ctx,
    redis_ctx,
    shared_config_ctx,
)

FIXTURES_WITH_NOASSOC = [
    {
        "groups": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "name": "mock_group",
                "description": "",
                "is_active": True,
                "domain_name": "default",
                "resource_policy": "default",
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "type": "general",
            }
        ],
        "container_registries": [
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "url": "https://mock.registry.com",
                "type": "docker",
                "project": "mock_project",
                "registry_name": "mock_registry",
            }
        ],
    }
]

FIXTURES_WITH_ASSOC = [
    {
        **fixture,
        "association_container_registries_groups": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "group_id": "00000000-0000-0000-0000-000000000001",
                "registry_id": "00000000-0000-0000-0000-000000000002",
            }
        ],
    }
    for fixture in FIXTURES_WITH_NOASSOC
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_fixtures",
    FIXTURES_WITH_NOASSOC + FIXTURES_WITH_ASSOC,
    ids=["(No association)", "(With association)"],
)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "group_id": "00000000-0000-0000-0000-000000000001",
            "registry_id": "00000000-0000-0000-0000-000000000002",
        },
    ],
    ids=["Associate One group with one container registry"],
)
async def test_associate_container_registry_with_group(
    test_case,
    etcd_fixture,
    extra_fixtures,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    app, client = await create_app_and_client(
        [
            shared_config_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
        ],
        [".container_registry", ".auth"],
    )

    group_id = test_case["group_id"]
    registry_id = test_case["registry_id"]

    url = f"/container-registries/{registry_id}"
    params = {"allowed_groups": {"add": [group_id]}}

    req_bytes = json.dumps(params).encode()
    headers = get_headers("PATCH", url, req_bytes)

    resp = await client.patch(url, data=req_bytes, headers=headers)
    association_exist = "association_container_registries_groups" in extra_fixtures

    if association_exist:
        assert resp.status == 400
    else:
        assert resp.status == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_fixtures",
    FIXTURES_WITH_ASSOC + FIXTURES_WITH_NOASSOC,
    ids=["(With association)", "(No association)"],
)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "group_id": "00000000-0000-0000-0000-000000000001",
            "registry_id": "00000000-0000-0000-0000-000000000002",
        },
    ],
    ids=["Disassociate One group with one container registry"],
)
async def test_disassociate_container_registry_with_group(
    test_case,
    etcd_fixture,
    extra_fixtures,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    app, client = await create_app_and_client(
        [
            shared_config_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
        ],
        [".container_registry", ".auth"],
    )

    group_id = test_case["group_id"]
    registry_id = test_case["registry_id"]

    url = f"/container-registries/{registry_id}"
    params = {"allowed_groups": {"remove": [group_id]}}

    req_bytes = json.dumps(params).encode()
    headers = get_headers("PATCH", url, req_bytes)

    resp = await client.patch(url, data=req_bytes, headers=headers)
    association_exist = "association_container_registries_groups" in extra_fixtures

    if association_exist:
        assert resp.status == 200
    else:
        assert resp.status == 404
