from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

from ai.backend.common.configs.loader import (
    ConfigOverrider,
    EnvLoader,
    EtcdConfigLoader,
    EtcdConfigWatcher,
    LoaderChain,
    TomlConfigLoader,
)
from ai.backend.common.configs.loader.types import AbstractConfigLoader


class CustomLoader(AbstractConfigLoader):
    async def load(self) -> dict[str, Any]:
        return {}


def test_abstract_default_source_name() -> None:
    loader = CustomLoader()
    assert loader.source_name == "CustomLoader"


def test_toml_loader_source_name() -> None:
    loader = TomlConfigLoader(Path("/etc/config.toml"), "manager")
    assert loader.source_name == "toml:/etc/config.toml"


def test_env_loader_source_name() -> None:
    loader = EnvLoader([])
    assert loader.source_name == "env"


def test_config_overrider_source_name() -> None:
    overrider = ConfigOverrider([])
    assert overrider.source_name == "overrides"


def test_etcd_loader_source_name() -> None:
    mock_etcd = AsyncMock()
    loader = EtcdConfigLoader(mock_etcd, prefix="ai/backend/config/common")
    assert loader.source_name == "etcd:ai/backend/config/common"


def test_etcd_watcher_source_name() -> None:
    mock_etcd = AsyncMock()
    watcher = EtcdConfigWatcher(mock_etcd, config_prefix="ai/backend/config")
    assert watcher.source_name == "etcd-watcher:ai/backend/config"


def test_loader_chain_source_name() -> None:
    chain = LoaderChain([
        EnvLoader([]),
        ConfigOverrider([]),
    ])
    assert chain.source_name == "chain:[env, overrides]"
