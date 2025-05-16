import json
from http import HTTPStatus
from urllib.parse import urlencode

import pytest
from aioresponses import aioresponses

from ai.backend.manager.server import (
    database_ctx,
    hook_plugin_ctx,
    monitoring_ctx,
    redis_ctx,
    services_ctx,
)
from ai.backend.testutils.extra_fixtures import FIXTURES_FOR_HARBOR_CRUD_TEST


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": -1},
                    }
                ],
            },
            "expected_code": 204,
        },
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": 100},
                    }
                ],
            },
            "expected_code": 400,
        },
    ],
    ids=["Normal case", "Project Quota already exist"],
)
async def test_harbor_create_project_quota(
    test_case,
    etcd_fixture,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    app, client = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
            services_ctx,
        ],
        [".group", ".auth"],
    )

    mock_harbor_responses = test_case["mock_harbor_responses"]

    url = "/group/registry-quota"
    params = {"group_id": "00000000-0000-0000-0000-000000000000", "quota": 100}
    req_bytes = json.dumps(params).encode()
    headers = get_headers("POST", url, req_bytes)

    with aioresponses(passthrough=["http://127.0.0.1"]) as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(
            get_project_id_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_project_id"],
        )

        harbor_project_id = mock_harbor_responses["get_project_id"]["project_id"]
        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={harbor_project_id}"
        mocked.get(
            get_quota_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_quotas"],
        )

        harbor_quota_id = mock_harbor_responses["get_quotas"][0]["id"]
        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{harbor_quota_id}"
        mocked.put(
            put_quota_url,
            status=HTTPStatus.OK,
        )

        resp = await client.post(url, data=req_bytes, headers=headers)
        assert resp.status == test_case["expected_code"]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": 100},
                    }
                ],
            },
            "expected_code": HTTPStatus.OK,
        },
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": -1},
                    }
                ],
            },
            "expected_code": HTTPStatus.NOT_FOUND,
        },
    ],
    ids=["Normal case", "Project Quota doesn't exist"],
)
async def test_harbor_read_project_quota(
    test_case,
    etcd_fixture,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    app, client = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
            services_ctx,
        ],
        [".group", ".auth"],
    )

    mock_harbor_responses = test_case["mock_harbor_responses"]

    with aioresponses(passthrough=["http://127.0.0.1"]) as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(
            get_project_id_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_project_id"],
        )
        harbor_project_id = mock_harbor_responses["get_project_id"]["project_id"]

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={harbor_project_id}"
        mocked.get(
            get_quota_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_quotas"],
        )

        url = "/group/registry-quota"
        params = {"group_id": "00000000-0000-0000-0000-000000000000"}
        full_url = f"{url}?{urlencode(params)}"
        headers = get_headers("GET", full_url, b"")

        resp = await client.get(url, params=params, headers=headers)
        assert resp.status == test_case["expected_code"]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": 100},
                    }
                ],
            },
            "expected_code": HTTPStatus.NO_CONTENT,
        },
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": -1},
                    }
                ],
            },
            "expected_code": HTTPStatus.NOT_FOUND,
        },
    ],
    ids=["Normal case", "Project Quota not found"],
)
async def test_harbor_update_project_quota(
    test_case,
    etcd_fixture,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    app, client = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
            services_ctx,
        ],
        [".group", ".auth"],
    )

    mock_harbor_responses = test_case["mock_harbor_responses"]

    url = "/group/registry-quota"
    params = {"group_id": "00000000-0000-0000-0000-000000000000", "quota": 200}
    req_bytes = json.dumps(params).encode()
    headers = get_headers("PATCH", url, req_bytes)

    with aioresponses(passthrough=["http://127.0.0.1"]) as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(
            get_project_id_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_project_id"],
        )
        harbor_project_id = mock_harbor_responses["get_project_id"]["project_id"]

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={harbor_project_id}"
        mocked.get(
            get_quota_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_quotas"],
        )
        harbor_quota_id = mock_harbor_responses["get_quotas"][0]["id"]

        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{harbor_quota_id}"
        mocked.put(
            put_quota_url,
            status=HTTPStatus.OK,
        )

        resp = await client.patch(url, data=req_bytes, headers=headers)
        assert resp.status == test_case["expected_code"]


@pytest.mark.asyncio
@pytest.mark.parametrize("extra_fixtures", FIXTURES_FOR_HARBOR_CRUD_TEST)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": 100},
                    }
                ],
            },
            "expected_code": HTTPStatus.NO_CONTENT,
        },
        {
            "mock_harbor_responses": {
                "get_project_id": {"project_id": "1"},
                "get_quotas": [
                    {
                        "id": 1,
                        "hard": {"storage": -1},
                    }
                ],
            },
            "expected_code": HTTPStatus.NOT_FOUND,
        },
    ],
    ids=["Normal case", "Project Quota not found"],
)
async def test_harbor_delete_project_quota(
    test_case,
    etcd_fixture,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    app, client = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
            services_ctx,
        ],
        [".group", ".auth"],
    )

    mock_harbor_responses = test_case["mock_harbor_responses"]

    url = "/group/registry-quota"
    params = {"group_id": "00000000-0000-0000-0000-000000000000"}
    req_bytes = json.dumps(params).encode()
    headers = get_headers("DELETE", url, req_bytes)

    with aioresponses(passthrough=["http://127.0.0.1"]) as mocked:
        get_project_id_url = "http://mock_registry/api/v2.0/projects/mock_project"
        mocked.get(
            get_project_id_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_project_id"],
        )
        harbor_project_id = mock_harbor_responses["get_project_id"]["project_id"]

        get_quota_url = f"http://mock_registry/api/v2.0/quotas?reference=project&reference_id={harbor_project_id}"
        mocked.get(
            get_quota_url,
            status=HTTPStatus.OK,
            payload=mock_harbor_responses["get_quotas"],
        )
        harbor_quota_id = mock_harbor_responses["get_quotas"][0]["id"]

        put_quota_url = f"http://mock_registry/api/v2.0/quotas/{harbor_quota_id}"
        mocked.put(
            put_quota_url,
            status=HTTPStatus.OK,
        )

        resp = await client.delete(url, data=req_bytes, headers=headers)
        assert resp.status == test_case["expected_code"]
