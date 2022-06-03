from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_register_myself(shared_config, mocker):
    instance_id = 'i-test-manager'
    from ai.backend.manager import config as config_mod
    mocked_get_instance_id = AsyncMock(return_value=instance_id)
    mocker.patch.object(config_mod, 'get_instance_id', mocked_get_instance_id)

    await shared_config.register_myself()
    mocked_get_instance_id.await_count == 1
    data = await shared_config.etcd.get_prefix(f'nodes/manager/{instance_id}')
    assert data[''] == 'up'

    await shared_config.deregister_myself()
    mocked_get_instance_id.await_count == 2
    data = await shared_config.etcd.get_prefix(f'nodes/manager/{instance_id}')
    assert len(data) == 0
