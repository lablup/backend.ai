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


class TestValkeySentinelClientPasswordUsage:
    """Verify sentinel_password goes to sentinel_kwargs, password (master) to GlideClient."""

    @pytest.fixture
    def target_with_separate_passwords(self) -> ValkeySentinelTarget:
        return ValkeySentinelTarget(
            sentinel_addresses=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-secret",
            sentinel_password="sentinel-secret",
        )

    @pytest.fixture
    def target_without_sentinel_password(self) -> ValkeySentinelTarget:
        return ValkeySentinelTarget(
            sentinel_addresses=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-secret",
        )

    def test_uses_sentinel_password_for_sentinel_kwargs(
        self, target_with_separate_passwords: ValkeySentinelTarget
    ) -> None:
        with patch("ai.backend.common.clients.valkey_client.client.Sentinel") as mock_sentinel_cls:
            ValkeySentinelClient(
                target=target_with_separate_passwords,
                db_id=0,
                human_readable_name="test",
            )
            sentinel_kwargs = mock_sentinel_cls.call_args.kwargs["sentinel_kwargs"]
            assert sentinel_kwargs["password"] == "sentinel-secret"

    def test_falls_back_to_password_when_sentinel_password_is_none(
        self, target_without_sentinel_password: ValkeySentinelTarget
    ) -> None:
        with patch("ai.backend.common.clients.valkey_client.client.Sentinel") as mock_sentinel_cls:
            ValkeySentinelClient(
                target=target_without_sentinel_password,
                db_id=0,
                human_readable_name="test",
            )
            sentinel_kwargs = mock_sentinel_cls.call_args.kwargs["sentinel_kwargs"]
            assert sentinel_kwargs["password"] == "master-secret"

    async def test_uses_password_for_glide_client_credentials(
        self, target_with_separate_passwords: ValkeySentinelTarget
    ) -> None:
        client = ValkeySentinelClient(
            target=target_with_separate_passwords,
            db_id=0,
            human_readable_name="test",
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
        assert target.password == "master-pw"

    def test_valkey_target_sentinel_password_defaults_to_none(self) -> None:
        target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-pw",
        )
        assert target.sentinel_password is None

    def test_sentinel_target_from_valkey_target_preserves_both(self) -> None:
        valkey_target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-pw",
            sentinel_password="sentinel-pw",
        )
        sentinel_target = ValkeySentinelTarget.from_valkey_target(valkey_target)
        assert sentinel_target.password == "master-pw"
        assert sentinel_target.sentinel_password == "sentinel-pw"

    def test_redis_target_to_valkey_target(self) -> None:
        redis_target = RedisTarget(
            sentinel="127.0.0.1:26379",
            service_name="mymaster",
            password="master-pw",
            sentinel_password="sentinel-pw",
        )
        valkey_target = redis_target.to_valkey_target()
        assert valkey_target.password == "master-pw"
        assert valkey_target.sentinel_password == "sentinel-pw"

    def test_redis_target_copy(self) -> None:
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
        assert valkey_target.password == "master-pw"
        assert valkey_target.sentinel_password == "sentinel-pw"

    def test_single_redis_config_to_redis_target(self) -> None:
        config = SingleRedisConfig.model_validate({
            "sentinel": "127.0.0.1:26379",
            "service_name": "mymaster",
            "password": "master-pw",
            "sentinel_password": "sentinel-pw",
        })
        redis_target = config.to_redis_target()
        assert redis_target.password == "master-pw"
        assert redis_target.sentinel_password == "sentinel-pw"

    def test_create_valkey_client_propagates_both(self) -> None:
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

        assert operation_client._target.password == "master-pw"
        assert operation_client._target.sentinel_password == "sentinel-pw"
        assert monitor_client._target.password == "master-pw"
        assert monitor_client._target.sentinel_password == "sentinel-pw"
