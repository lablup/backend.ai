from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.clients.valkey_client.client import (
    MonitoringValkeyClient,
    ValkeySentinelClient,
    ValkeySentinelTarget,
    create_valkey_client,
)
from ai.backend.common.configs.redis import SingleRedisConfig
from ai.backend.common.types import RedisTarget, ValkeyTarget

MASTER_PASSWORD = "master-pw"
SENTINEL_PASSWORD = "sentinel-pw"


@pytest.fixture
def valkey_target_with_separate_passwords() -> ValkeyTarget:
    return ValkeyTarget(
        sentinel=["127.0.0.1:26379"],
        service_name="mymaster",
        password=MASTER_PASSWORD,
        sentinel_password=SENTINEL_PASSWORD,
    )


@pytest.fixture
def valkey_target_without_sentinel_password() -> ValkeyTarget:
    return ValkeyTarget(
        sentinel=["127.0.0.1:26379"],
        service_name="mymaster",
        password=MASTER_PASSWORD,
    )


@pytest.fixture
def sentinel_target_with_separate_passwords() -> ValkeySentinelTarget:
    return ValkeySentinelTarget(
        sentinel_addresses=["127.0.0.1:26379"],
        service_name="mymaster",
        password=MASTER_PASSWORD,
        sentinel_password=SENTINEL_PASSWORD,
    )


@pytest.fixture
def sentinel_target_without_sentinel_password() -> ValkeySentinelTarget:
    return ValkeySentinelTarget(
        sentinel_addresses=["127.0.0.1:26379"],
        service_name="mymaster",
        password=MASTER_PASSWORD,
    )


@pytest.fixture
def sentinel_client_with_separate_passwords(
    sentinel_target_with_separate_passwords: ValkeySentinelTarget,
) -> ValkeySentinelClient:
    with patch("ai.backend.common.clients.valkey_client.client.Sentinel"):
        return ValkeySentinelClient(
            target=sentinel_target_with_separate_passwords,
            db_id=0,
            human_readable_name="test",
        )


@pytest.fixture
def sentinel_client_connected_with_separate_passwords(
    sentinel_target_with_separate_passwords: ValkeySentinelTarget,
) -> ValkeySentinelClient:
    with patch("ai.backend.common.clients.valkey_client.client.Sentinel"):
        client = ValkeySentinelClient(
            target=sentinel_target_with_separate_passwords,
            db_id=0,
            human_readable_name="test",
        )
    client._sentinel = MagicMock()
    client._sentinel.discover_master = AsyncMock(return_value=("127.0.0.1", 6379))
    return client


@pytest.fixture
def redis_target_with_separate_passwords() -> RedisTarget:
    return RedisTarget(
        sentinel="127.0.0.1:26379",
        service_name="mymaster",
        password=MASTER_PASSWORD,
        sentinel_password=SENTINEL_PASSWORD,
    )


@pytest.fixture
def single_redis_config_with_separate_passwords() -> SingleRedisConfig:
    return SingleRedisConfig.model_validate({
        "sentinel": "127.0.0.1:26379",
        "service_name": "mymaster",
        "password": MASTER_PASSWORD,
        "sentinel_password": SENTINEL_PASSWORD,
    })


class TestValkeySentinelClientPasswordUsage:
    """Verify sentinel_password goes to sentinel_kwargs, password (master) to GlideClient."""

    def test_uses_sentinel_password_for_sentinel_kwargs(
        self, sentinel_target_with_separate_passwords: ValkeySentinelTarget
    ) -> None:
        with patch("ai.backend.common.clients.valkey_client.client.Sentinel") as mock_sentinel_cls:
            ValkeySentinelClient(
                target=sentinel_target_with_separate_passwords,
                db_id=0,
                human_readable_name="test",
            )
            sentinel_kwargs = mock_sentinel_cls.call_args.kwargs["sentinel_kwargs"]
            assert sentinel_kwargs["password"] == SENTINEL_PASSWORD

    def test_falls_back_to_password_when_sentinel_password_is_none(
        self, sentinel_target_without_sentinel_password: ValkeySentinelTarget
    ) -> None:
        with patch("ai.backend.common.clients.valkey_client.client.Sentinel") as mock_sentinel_cls:
            ValkeySentinelClient(
                target=sentinel_target_without_sentinel_password,
                db_id=0,
                human_readable_name="test",
            )
            sentinel_kwargs = mock_sentinel_cls.call_args.kwargs["sentinel_kwargs"]
            assert sentinel_kwargs["password"] == MASTER_PASSWORD

    async def test_uses_password_for_glide_client_credentials(
        self,
        sentinel_client_connected_with_separate_passwords: ValkeySentinelClient,
    ) -> None:
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
            await sentinel_client_connected_with_separate_passwords.connect()

            mock_credentials.assert_called_once_with(password=MASTER_PASSWORD)


class TestSentinelPasswordPropagation:
    """Verify sentinel_password is propagated through all conversion paths."""

    def test_valkey_target_carries_both(
        self, valkey_target_with_separate_passwords: ValkeyTarget
    ) -> None:
        assert valkey_target_with_separate_passwords.password == MASTER_PASSWORD
        assert valkey_target_with_separate_passwords.sentinel_password == SENTINEL_PASSWORD

    def test_valkey_target_sentinel_password_defaults_to_none(
        self, valkey_target_without_sentinel_password: ValkeyTarget
    ) -> None:
        assert valkey_target_without_sentinel_password.sentinel_password is None

    def test_sentinel_target_from_valkey_target(
        self, valkey_target_with_separate_passwords: ValkeyTarget
    ) -> None:
        sentinel_target = ValkeySentinelTarget.from_valkey_target(
            valkey_target_with_separate_passwords
        )
        assert sentinel_target.password == MASTER_PASSWORD
        assert sentinel_target.sentinel_password == SENTINEL_PASSWORD

    def test_redis_target_to_valkey_target(
        self, redis_target_with_separate_passwords: RedisTarget
    ) -> None:
        valkey_target = redis_target_with_separate_passwords.to_valkey_target()
        assert valkey_target.password == MASTER_PASSWORD
        assert valkey_target.sentinel_password == SENTINEL_PASSWORD

    def test_redis_target_copy(self, redis_target_with_separate_passwords: RedisTarget) -> None:
        copied = redis_target_with_separate_passwords.copy()
        assert copied.sentinel_password == SENTINEL_PASSWORD

    def test_single_redis_config_to_valkey_target(
        self, single_redis_config_with_separate_passwords: SingleRedisConfig
    ) -> None:
        valkey_target = single_redis_config_with_separate_passwords.to_valkey_target()
        assert valkey_target.password == MASTER_PASSWORD
        assert valkey_target.sentinel_password == SENTINEL_PASSWORD

    def test_single_redis_config_to_redis_target(
        self, single_redis_config_with_separate_passwords: SingleRedisConfig
    ) -> None:
        redis_target = single_redis_config_with_separate_passwords.to_redis_target()
        assert redis_target.password == MASTER_PASSWORD
        assert redis_target.sentinel_password == SENTINEL_PASSWORD

    def test_create_valkey_client_propagates_both(
        self, valkey_target_with_separate_passwords: ValkeyTarget
    ) -> None:
        client = create_valkey_client(
            valkey_target_with_separate_passwords, db_id=0, human_readable_name="test"
        )

        assert isinstance(client, MonitoringValkeyClient)
        operation_client = client._operation_client
        monitor_client = client._monitor_client
        assert isinstance(operation_client, ValkeySentinelClient)
        assert isinstance(monitor_client, ValkeySentinelClient)

        assert operation_client._target.password == MASTER_PASSWORD
        assert operation_client._target.sentinel_password == SENTINEL_PASSWORD
        assert monitor_client._target.password == MASTER_PASSWORD
        assert monitor_client._target.sentinel_password == SENTINEL_PASSWORD
