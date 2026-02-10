from unittest.mock import AsyncMock

from ai.backend.common.configs.loader import EtcdConfigWatcher


def test_etcd_watcher_default_prefix() -> None:
    mock_etcd = AsyncMock()
    watcher = EtcdConfigWatcher(mock_etcd)
    assert watcher._config_prefix == "ai/backend/config"


def test_etcd_watcher_custom_prefix() -> None:
    mock_etcd = AsyncMock()
    watcher = EtcdConfigWatcher(mock_etcd, config_prefix="custom/prefix")
    assert watcher._config_prefix == "custom/prefix"


def test_etcd_watcher_source_name() -> None:
    mock_etcd = AsyncMock()
    watcher = EtcdConfigWatcher(mock_etcd, config_prefix="my/prefix")
    assert watcher.source_name == "etcd-watcher:my/prefix"
