from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.common.clients.valkey_client.client import (
    MonitoringValkeyClient,
    ValkeySentinelClient,
    ValkeySentinelTarget,
    create_valkey_client,
)
from ai.backend.common.configs.redis import SingleRedisConfig
from ai.backend.common.types import RedisTarget, ValkeyTarget


class TestValkeySentinelTargetPasswordResolution:
    """Verify from_valkey_target() resolves sentinel password with fallback at construction time."""

    def test_sentinel_password_takes_precedence(self) -> None:
        valkey_target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-pw",
            sentinel_password="sentinel-pw",
        )
        sentinel_target = ValkeySentinelTarget.from_valkey_target(valkey_target)
        assert sentinel_target.password == "sentinel-pw"

    def test_falls_back_to_master_password_when_sentinel_password_is_none(self) -> None:
        valkey_target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-pw",
        )
        sentinel_target = ValkeySentinelTarget.from_valkey_target(valkey_target)
        assert sentinel_target.password == "master-pw"

    def test_no_master_password_on_sentinel_target(self) -> None:
        sentinel_target = ValkeySentinelTarget(
            sentinel_addresses=["127.0.0.1:26379"],
            service_name="mymaster",
            password="sentinel-pw",
        )
        assert not hasattr(sentinel_target, "master_password")


class TestValkeySentinelClientPasswordUsage:
    """Verify sentinel password goes to sentinel_kwargs, master password to GlideClient."""

    @pytest.fixture
    def sentinel_target(self) -> ValkeySentinelTarget:
        return ValkeySentinelTarget(
            sentinel_addresses=["127.0.0.1:26379"],
            service_name="mymaster",
            password="sentinel-secret",
        )

    def test_sentinel_kwargs_uses_target_password(
        self, sentinel_target: ValkeySentinelTarget
    ) -> None:
        with patch("ai.backend.common.clients.valkey_client.client.Sentinel") as mock_sentinel_cls:
            ValkeySentinelClient(
                target=sentinel_target,
                db_id=0,
                human_readable_name="test",
                master_password="master-secret",
            )
            sentinel_kwargs = mock_sentinel_cls.call_args.kwargs["sentinel_kwargs"]
            assert sentinel_kwargs["password"] == "sentinel-secret"

    async def test_glide_client_uses_master_password(
        self, sentinel_target: ValkeySentinelTarget
    ) -> None:
        client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test",
            master_password="master-secret",
        )
        client._sentinel = AsyncMock()
        client._sentinel.discover_master = AsyncMock(return_value=("127.0.0.1", 6379))

        with (
            patch(
                "ai.backend.common.clients.valkey_client.client.GlideClient.create",
                new_callable=AsyncMock,
            ) as mock_create,
            patch(
                "ai.backend.common.clients.valkey_client.client.ServerCredentials",
            ) as mock_credentials,
        ):
            mock_create.return_value = AsyncMock()
            await client.connect()

            mock_credentials.assert_called_once_with(password="master-secret")


class TestSentinelPasswordPropagation:
    """Verify sentinel_password is propagated through all conversion paths."""

    def test_valkey_target_carries_sentinel_password(self) -> None:
        target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-pw",
            sentinel_password="sentinel-pw",
        )
        assert target.sentinel_password == "sentinel-pw"

    def test_redis_target_to_valkey_target_preserves_sentinel_password(self) -> None:
        redis_target = RedisTarget(
            sentinel="127.0.0.1:26379",
            service_name="mymaster",
            password="master-pw",
            sentinel_password="sentinel-pw",
        )
        valkey_target = redis_target.to_valkey_target()
        assert valkey_target.sentinel_password == "sentinel-pw"
        assert valkey_target.password == "master-pw"

    def test_redis_target_copy_preserves_sentinel_password(self) -> None:
        original = RedisTarget(
            sentinel="127.0.0.1:26379",
            service_name="mymaster",
            password="master-pw",
            sentinel_password="sentinel-pw",
        )
        copied = original.copy()
        assert copied.sentinel_password == "sentinel-pw"

    def test_single_redis_config_to_valkey_target(self) -> None:
        config = SingleRedisConfig.model_validate({
            "sentinel": "127.0.0.1:26379",
            "service_name": "mymaster",
            "password": "master-pw",
            "sentinel_password": "sentinel-pw",
        })
        valkey_target = config.to_valkey_target()
        assert valkey_target.sentinel_password == "sentinel-pw"
        assert valkey_target.password == "master-pw"

    def test_single_redis_config_to_redis_target(self) -> None:
        config = SingleRedisConfig.model_validate({
            "sentinel": "127.0.0.1:26379",
            "service_name": "mymaster",
            "password": "master-pw",
            "sentinel_password": "sentinel-pw",
        })
        redis_target = config.to_redis_target()
        assert redis_target.sentinel_password == "sentinel-pw"
        assert redis_target.password == "master-pw"

    def test_create_valkey_client_resolves_passwords(self) -> None:
        target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-pw",
            sentinel_password="sentinel-pw",
        )
        client = create_valkey_client(target, db_id=0, human_readable_name="test")

        assert isinstance(client, MonitoringValkeyClient)
        operation_client = client._operation_client
        monitor_client = client._monitor_client
        assert isinstance(operation_client, ValkeySentinelClient)
        assert isinstance(monitor_client, ValkeySentinelClient)

        # ValkeySentinelTarget.password = resolved sentinel password
        assert operation_client._target.password == "sentinel-pw"
        assert monitor_client._target.password == "sentinel-pw"
        # master_password passed separately to ValkeySentinelClient
        assert operation_client._master_password == "master-pw"
        assert monitor_client._master_password == "master-pw"

    def test_valkey_target_sentinel_password_defaults_to_none(self) -> None:
        target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-pw",
        )
        assert target.sentinel_password is None
