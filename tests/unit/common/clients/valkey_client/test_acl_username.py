from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.clients.valkey_client.client import (
    MonitoringValkeyClient,
    ValkeySentinelClient,
    ValkeySentinelTarget,
    ValkeyStandaloneClient,
    ValkeyStandaloneTarget,
    create_valkey_client,
)
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.defs import RedisRole
from ai.backend.common.types import RedisProfileTarget, RedisTarget, ValkeyTarget

ACL_USERNAME = "agent"
OVERRIDE_USERNAME = "stream-agent"
PASSWORD = "master-pw"
SENTINEL_PASSWORD = "sentinel-pw"


@pytest.fixture
def standalone_target() -> ValkeyStandaloneTarget:
    return ValkeyStandaloneTarget(
        address="127.0.0.1:6379", username=ACL_USERNAME, password=PASSWORD
    )


@pytest.fixture
def standalone_target_without_username() -> ValkeyStandaloneTarget:
    return ValkeyStandaloneTarget(address="127.0.0.1:6379", password=PASSWORD)


@pytest.fixture
def sentinel_target() -> ValkeySentinelTarget:
    return ValkeySentinelTarget(
        sentinel_addresses=["127.0.0.1:26379"],
        service_name="mymaster",
        username=ACL_USERNAME,
        password=PASSWORD,
        sentinel_password=SENTINEL_PASSWORD,
    )


@pytest.fixture
def sentinel_target_without_username() -> ValkeySentinelTarget:
    return ValkeySentinelTarget(
        sentinel_addresses=["127.0.0.1:26379"],
        service_name="mymaster",
        password=PASSWORD,
    )


@pytest.fixture
def valkey_sentinel_target() -> ValkeyTarget:
    return ValkeyTarget(
        sentinel=["127.0.0.1:26379"],
        service_name="mymaster",
        username=ACL_USERNAME,
        password=PASSWORD,
    )


@pytest.fixture
def valkey_standalone_target() -> ValkeyTarget:
    return ValkeyTarget(addr="127.0.0.1:6379", username=ACL_USERNAME, password=PASSWORD)


@pytest.fixture
def redis_target() -> RedisTarget:
    return RedisTarget(username=ACL_USERNAME, password=PASSWORD)


@pytest.fixture
def redis_config() -> RedisConfig:
    return RedisConfig.model_validate({
        "addr": {"host": "127.0.0.1", "port": 6379},
        "username": ACL_USERNAME,
        "password": PASSWORD,
        "override-configs": {
            RedisRole.STREAM: {
                "addr": {"host": "127.0.0.1", "port": 6380},
                "username": OVERRIDE_USERNAME,
                "password": PASSWORD,
            },
        },
    })


async def _connect_with_mocked_credentials(client: Any) -> MagicMock:
    with (
        patch(
            "ai.backend.common.clients.valkey_client.client.GlideClient.create",
            new_callable=AsyncMock,
        ) as mock_create,
        patch("ai.backend.common.clients.valkey_client.client.ServerCredentials") as mock_cred,
    ):
        mock_create.return_value = AsyncMock()
        await client.connect()
    return mock_cred


class TestGlideCredentials:
    async def test_standalone_passes_username_and_password(
        self, standalone_target: ValkeyStandaloneTarget
    ) -> None:
        client = ValkeyStandaloneClient(standalone_target, db_id=0, human_readable_name="test")
        mock_cred = await _connect_with_mocked_credentials(client)
        mock_cred.assert_called_once_with(password=PASSWORD, username=ACL_USERNAME)

    async def test_standalone_without_username_keeps_default_user(
        self, standalone_target_without_username: ValkeyStandaloneTarget
    ) -> None:
        client = ValkeyStandaloneClient(
            standalone_target_without_username, db_id=0, human_readable_name="test"
        )
        mock_cred = await _connect_with_mocked_credentials(client)
        mock_cred.assert_called_once_with(password=PASSWORD, username=None)

    async def test_sentinel_master_passes_username_and_password(
        self, sentinel_target: ValkeySentinelTarget
    ) -> None:
        with patch("ai.backend.common.clients.valkey_client.client.Sentinel"):
            client = ValkeySentinelClient(sentinel_target, db_id=0, human_readable_name="test")
        client._sentinel = MagicMock()
        client._sentinel.discover_master = AsyncMock(return_value=("127.0.0.1", 6379))
        mock_cred = await _connect_with_mocked_credentials(client)
        mock_cred.assert_called_once_with(password=PASSWORD, username=ACL_USERNAME)

    def test_sentinel_kwargs_never_carry_username(
        self, sentinel_target: ValkeySentinelTarget
    ) -> None:
        with patch("ai.backend.common.clients.valkey_client.client.Sentinel") as mock_sentinel_cls:
            ValkeySentinelClient(sentinel_target, db_id=0, human_readable_name="test")
        sentinel_kwargs = mock_sentinel_cls.call_args.kwargs["sentinel_kwargs"]
        assert sentinel_kwargs["password"] == SENTINEL_PASSWORD
        assert "username" not in sentinel_kwargs


class TestUsernamePropagation:
    def test_standalone_target_from_valkey_target(
        self, valkey_standalone_target: ValkeyTarget
    ) -> None:
        target = ValkeyStandaloneTarget.from_valkey_target(valkey_standalone_target)
        assert target.username == ACL_USERNAME

    def test_sentinel_target_from_valkey_target(self, valkey_sentinel_target: ValkeyTarget) -> None:
        target = ValkeySentinelTarget.from_valkey_target(valkey_sentinel_target)
        assert target.username == ACL_USERNAME

    def test_redis_target_copy_and_to_valkey_target(self, redis_target: RedisTarget) -> None:
        assert redis_target.copy().username == ACL_USERNAME
        assert redis_target.to_valkey_target().username == ACL_USERNAME

    def test_redis_profile_target_from_dict(self) -> None:
        profile = RedisProfileTarget.from_dict({
            "addr": "127.0.0.1:6379",
            "username": ACL_USERNAME,
            "password": PASSWORD,
            "override_configs": {
                RedisRole.STREAM: {"addr": "127.0.0.1:6380", "username": OVERRIDE_USERNAME},
            },
        })
        assert profile.profile_target(RedisRole.LIVE).username == ACL_USERNAME
        assert profile.profile_target(RedisRole.STREAM).username == OVERRIDE_USERNAME

    def test_redis_config_to_valkey_profile_target(self, redis_config: RedisConfig) -> None:
        profile = redis_config.to_valkey_profile_target()
        assert profile.profile_target(RedisRole.LIVE).username == ACL_USERNAME
        assert profile.profile_target(RedisRole.STREAM).username == OVERRIDE_USERNAME

    def test_redis_config_to_redis_profile_target(self, redis_config: RedisConfig) -> None:
        profile = redis_config.to_redis_profile_target()
        assert profile.profile_target(RedisRole.LIVE).username == ACL_USERNAME
        assert profile.profile_target(RedisRole.STREAM).username == OVERRIDE_USERNAME

    def test_redis_config_to_single_targets(self, redis_config: RedisConfig) -> None:
        assert redis_config.to_valkey_target().username == ACL_USERNAME
        assert redis_config.to_redis_target().username == ACL_USERNAME

    def test_redis_config_username_defaults_to_none(self) -> None:
        config = RedisConfig.model_validate({"addr": {"host": "127.0.0.1", "port": 6379}})
        assert config.username is None
        assert config.to_valkey_target().username is None

    async def test_create_valkey_client_monitor_connects_with_username(
        self, valkey_sentinel_target: ValkeyTarget
    ) -> None:
        client = create_valkey_client(valkey_sentinel_target, db_id=0, human_readable_name="test")
        assert isinstance(client, MonitoringValkeyClient)
        for inner in (client._operation_client, client._monitor_client):
            assert isinstance(inner, ValkeySentinelClient)
            inner._sentinel = MagicMock()
            inner._sentinel.discover_master = AsyncMock(return_value=("127.0.0.1", 6379))
            mock_cred = await _connect_with_mocked_credentials(inner)
            mock_cred.assert_called_once_with(password=PASSWORD, username=ACL_USERNAME)
