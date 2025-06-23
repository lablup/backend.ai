from unittest.mock import AsyncMock

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader


@pytest.mark.asyncio
async def test_register_myself(bootstrap_config, mocker):
    instance_id = "i-test-manager"
    from ai.backend.manager.config.loader import legacy_etcd_loader as loader_mod

    mocked_get_instance_id = AsyncMock(return_value=instance_id)
    mocker.patch.object(loader_mod, "get_instance_id", mocked_get_instance_id)

    etcd = AsyncEtcd.initialize(bootstrap_config.etcd.to_dataclass())
    etcd_loader = LegacyEtcdLoader(etcd)

    await etcd_loader.register_myself()
    assert mocked_get_instance_id.await_count == 1
    data = await etcd.get_prefix(f"nodes/manager/{instance_id}")
    assert data[""] == "up"

    await etcd_loader.deregister_myself()
    assert mocked_get_instance_id.await_count == 2
    data = await etcd.get_prefix(f"nodes/manager/{instance_id}")
    assert len(data) == 0
