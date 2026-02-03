from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.loader import legacy_etcd_loader as loader_mod
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader


@pytest.mark.asyncio
async def test_register_myself(bootstrap_config: Any, mocker: Any) -> None:
    instance_id = "i-test-manager"

    mocked_get_instance_id = AsyncMock(return_value=instance_id)
    mocker.patch.object(loader_mod, "get_instance_id", mocked_get_instance_id)

    async with AsyncEtcd.create_from_config(bootstrap_config.etcd.to_dataclass()) as etcd:
        etcd_loader = LegacyEtcdLoader(etcd)

        await etcd_loader.register_myself()
        assert mocked_get_instance_id.await_count == 1
        data = await etcd.get_prefix(f"nodes/manager/{instance_id}")
        assert data[""] == "up"

        await etcd_loader.deregister_myself()
        assert mocked_get_instance_id.await_count == 2
        data = await etcd.get_prefix(f"nodes/manager/{instance_id}")
        assert len(data) == 0
