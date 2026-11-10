from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.configs.loader import AbstractConfigLoader, LoaderChain
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader


def _etcd_with(values: Mapping[str, Any]) -> AsyncEtcd:
    etcd = MagicMock(spec=AsyncEtcd)
    etcd.get_prefix = AsyncMock(return_value=values)
    return etcd


def _static_loader(values: Mapping[str, Any]) -> AbstractConfigLoader:
    loader = MagicMock(spec=AbstractConfigLoader)
    loader.load = AsyncMock(return_value=values)
    return loader


class TestLegacyEtcdLoader:
    @pytest.mark.parametrize(
        ("etcd_config", "expected"),
        [
            pytest.param(
                {"redis": {"addr": "127.0.0.1:6379"}, "system": {"timezone": "UTC"}},
                {"system": {"timezone": "UTC"}},
                id="redis",
            ),
            pytest.param(
                {"system": {"timezone": "UTC"}},
                {"system": {"timezone": "UTC"}},
                id="no-redis",
            ),
        ],
    )
    async def test_ignores_redis(
        self, etcd_config: Mapping[str, Any], expected: Mapping[str, Any]
    ) -> None:
        loaded = await LegacyEtcdLoader(_etcd_with(etcd_config)).load()

        assert loaded == expected

    async def test_local_redis_survives_merge(self) -> None:
        local = _static_loader({"redis": {"addr": "10.0.0.1:6379", "password": "local"}})
        etcd = _etcd_with({"redis": {"addr": "10.0.0.2:6379", "password": "remote"}})

        loaded = await LoaderChain([local, LegacyEtcdLoader(etcd)]).load()

        assert loaded["redis"] == {"addr": "10.0.0.1:6379", "password": "local"}
