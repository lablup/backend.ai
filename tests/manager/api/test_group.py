import json
from urllib.parse import urlencode

import pytest
from aioresponses import aioresponses

from ai.backend.manager.server import (
    database_ctx,
    hook_plugin_ctx,
    monitoring_ctx,
    redis_ctx,
    shared_config_ctx,
)

FIXTURES_FOR_HARBOR_CRUD_TEST = [
    {
        "container_registries": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "type": "harbor2",
                "url": "http://mock_registry",
                "registry_name": "mock_registry",
                "project": "mock_project",
                "username": "mock_user",
                "password": "mock_password",
                "ssl_verify": False,
                "is_global": True,
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
                "container_registry": {
                    "registry": "mock_registry",
                    "project": "mock_project",
                },
                "type": "general",
            }
        ],
    },
]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
async def test_harbor_read_project_quota(
    etcd_fixture,
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
        [".group", ".auth"],
    )

    HARBOR_PROJECT_ID = "123"
    HARBOR_QUOTA_ID = 456
    HARBOR_QUOTA_VALUE = 1024

    with aioresponses(passthrough=["http://127.0.0.1"]) as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": HARBOR_QUOTA_VALUE}}],
        )

        url = "/group/registry-quota"
        params = {"group_id": "00000000-0000-0000-0000-000000000000"}
        full_url = f"{url}?{urlencode(params)}"
        headers = get_headers("GET", full_url, b"")

        resp = await client.get(url, params=params, headers=headers)
        assert resp.status == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
async def test_harbor_update_project_quota(
    etcd_fixture,
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
        [".group", ".auth"],
    )

    HARBOR_PROJECT_ID = "123"
    HARBOR_QUOTA_ID = 456
    HARBOR_QUOTA_VALUE = 1024

    # Normal case: update quota
    with aioresponses(passthrough=["http://127.0.0.1"]) as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": 100}}],
        )

        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{HARBOR_QUOTA_ID}"
        mocked.put(
            put_quota_url,
            status=200,
        )

        url = "/group/registry-quota"
        params = {"group_id": "00000000-0000-0000-0000-000000000000", "quota": HARBOR_QUOTA_VALUE}
        req_bytes = json.dumps(params).encode()
        headers = get_headers("PATCH", url, req_bytes)

        resp = await client.patch(url, data=req_bytes, headers=headers)
        assert resp.status == 200

    # If the quota doesn't exist, the mutation should fail
    with aioresponses(passthrough=["http://127.0.0.1"]) as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(get_project_id_url, status=200, payload={"project_id": HARBOR_PROJECT_ID})

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={HARBOR_PROJECT_ID}"
        mocked.get(
            get_quota_url,
            status=200,
            payload=[{"id": HARBOR_QUOTA_ID, "hard": {"storage": -1}}],
        )
        url = "/group/registry-quota"
        params = {"group_id": "00000000-0000-0000-0000-000000000000", "quota": HARBOR_QUOTA_VALUE}
        req_bytes = json.dumps(params).encode()
        headers = get_headers("PATCH", url, req_bytes)

        resp = await client.patch(url, data=req_bytes, headers=headers)
        assert resp.status == 404
