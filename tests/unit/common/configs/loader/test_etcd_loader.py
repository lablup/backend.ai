from unittest.mock import AsyncMock

from ai.backend.common.configs.loader import EtcdConfigLoader


async def test_etcd_config_loader_common_prefix() -> None:
    mock_etcd = AsyncMock()
    mock_etcd.get_prefix.return_value = {"key1": "value1"}

    loader = EtcdConfigLoader(mock_etcd, prefix="ai/backend/config/common")
    result = await loader.load()

    mock_etcd.get_prefix.assert_awaited_once_with("ai/backend/config/common")
    assert result == {"key1": "value1"}


async def test_etcd_config_loader_manager_prefix() -> None:
    mock_etcd = AsyncMock()
    mock_etcd.get_prefix.return_value = {"manager_key": "manager_value"}

    loader = EtcdConfigLoader(mock_etcd, prefix="ai/backend/config/manager")
    result = await loader.load()

    mock_etcd.get_prefix.assert_awaited_once_with("ai/backend/config/manager")
    assert result == {"manager_key": "manager_value"}


async def test_etcd_config_loader_custom_prefix() -> None:
    mock_etcd = AsyncMock()
    mock_etcd.get_prefix.return_value = {"custom": "data"}

    loader = EtcdConfigLoader(mock_etcd, prefix="my/custom/prefix")
    result = await loader.load()

    mock_etcd.get_prefix.assert_awaited_once_with("my/custom/prefix")
    assert result == {"custom": "data"}
