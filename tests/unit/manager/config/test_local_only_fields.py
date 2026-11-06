from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.configs.loader.local_only_filter import LocalOnlyFieldFilter
from ai.backend.common.configs.loader.types import AbstractConfigLoader
from ai.backend.manager.config.unified import ManagerUnifiedConfig


class TestManagerLocalOnlyFields:
    async def test_redis_passwords_and_storage_proxy_secret_are_local_only(self) -> None:
        etcd_loader = MagicMock(spec=AbstractConfigLoader)
        etcd_loader.source_name = "etcd:test"
        etcd_loader.load = AsyncMock(
            return_value={
                "redis": {
                    "addr": "redis:6379",
                    "password": "p",
                    "sentinel-password": "sp",
                    "override-configs": {"live": {"addr": "live:6379", "password": "p"}},
                },
                "volumes": {
                    "default_host": "local:volume1",
                    "proxies": {"local": {"client_api": "http://sp:6021", "secret": "s"}},
                },
            }
        )

        config = await LocalOnlyFieldFilter(etcd_loader, ManagerUnifiedConfig).load()

        assert config == {
            "redis": {
                "addr": "redis:6379",
                "override-configs": {"live": {"addr": "live:6379"}},
            },
            "volumes": {
                "default_host": "local:volume1",
                "proxies": {"local": {"client_api": "http://sp:6021"}},
            },
        }
