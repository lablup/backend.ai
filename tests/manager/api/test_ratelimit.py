import json

import pytest

import ai.backend.manager.api.ratelimit as rlim
from ai.backend.manager.server import (
    database_ctx,
    event_dispatcher_ctx,
    hook_plugin_ctx,
    monitoring_ctx,
    redis_ctx,
    shared_config_ctx,
)


@pytest.mark.asyncio
async def test_check_rlim_for_anonymous_query(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
):
    app, client = await create_app_and_client(
        [
            shared_config_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
        ],
        ['.auth', '.ratelimit'],
    )
    ret = await client.get('/')
    assert ret.status == 200
    assert '1000' == ret.headers['X-RateLimit-Limit']
    assert '1000' == ret.headers['X-RateLimit-Remaining']
    assert str(rlim._rlim_window) == ret.headers['X-RateLimit-Window']


@pytest.mark.asyncio
async def test_check_rlim_for_authorized_query(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    app, client = await create_app_and_client(
        [
            shared_config_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
        ],
        ['.auth', '.ratelimit'],
    )
    url = '/auth/test'
    req_bytes = json.dumps({'echo': 'hello!'}).encode()
    headers = get_headers('POST', url, req_bytes)
    ret = await client.post(url, data=req_bytes, headers=headers)

    assert ret.status == 200
    # The default example keypair's ratelimit is 30000.
    assert '30000' == ret.headers['X-RateLimit-Limit']
    assert '29999' == ret.headers['X-RateLimit-Remaining']
    assert str(rlim._rlim_window) == ret.headers['X-RateLimit-Window']
