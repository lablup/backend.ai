from __future__ import annotations

from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.redis_helper import (
    _parse_redis_url,
    create_valkey_client,
    get_redis_object,
    get_redis_object_for_lock,
)
from ai.backend.common.types import HostPortPair, RedisHelperConfig, RedisTarget, ValkeyTarget

ACL_USERNAME = "agent"
PASSWORD = "master-pw"
SENTINEL_PASSWORD = "sentinel-pw"

_REDIS_HELPER_CONFIG: RedisHelperConfig = {
    "socket_timeout": 5.0,
    "socket_connect_timeout": 2.0,
    "reconnect_poll_timeout": 0.3,
}

SentinelFactory = Callable[..., object]


@pytest.fixture
def standalone_target() -> RedisTarget:
    return RedisTarget(
        addr=HostPortPair("127.0.0.1", 6379),
        username=ACL_USERNAME,
        password=PASSWORD,
        redis_helper_config=_REDIS_HELPER_CONFIG,
    )


@pytest.fixture
def sentinel_target() -> RedisTarget:
    return RedisTarget(
        sentinel=[HostPortPair("127.0.0.1", 26379)],
        service_name="mymaster",
        username=ACL_USERNAME,
        password=PASSWORD,
        sentinel_password=SENTINEL_PASSWORD,
        redis_helper_config=_REDIS_HELPER_CONFIG,
    )


@pytest.fixture
def standalone_target_without_username() -> RedisTarget:
    return RedisTarget(addr=HostPortPair("127.0.0.1", 6379), password=PASSWORD)


@pytest.fixture
def sentinel_target_without_username() -> RedisTarget:
    return RedisTarget(
        sentinel=[HostPortPair("127.0.0.1", 26379)],
        service_name="mymaster",
        password=PASSWORD,
        redis_helper_config=_REDIS_HELPER_CONFIG,
    )


class TestParseRedisUrl:
    def test_url_carries_username_and_password(self, standalone_target: RedisTarget) -> None:
        url = _parse_redis_url(standalone_target, 3)
        assert url.user == ACL_USERNAME
        assert url.password == PASSWORD
        assert url.path == "/3"

    def test_url_without_username_has_no_user(
        self, standalone_target_without_username: RedisTarget
    ) -> None:
        url = _parse_redis_url(standalone_target_without_username, 0)
        assert url.user is None
        assert url.password == PASSWORD


class TestSentinelMasterAuth:
    @pytest.mark.parametrize("factory", [get_redis_object, get_redis_object_for_lock])
    def test_master_for_gets_username_but_sentinel_kwargs_do_not(
        self, factory: SentinelFactory, sentinel_target: RedisTarget
    ) -> None:
        with patch("ai.backend.common.redis_helper.Sentinel") as mock_sentinel_cls:
            mock_sentinel_cls.return_value = MagicMock()
            factory(sentinel_target, name="test", db=0)
        master_kwargs = mock_sentinel_cls.return_value.master_for.call_args.kwargs
        assert master_kwargs["username"] == ACL_USERNAME
        assert master_kwargs["password"] == PASSWORD
        sentinel_kwargs = mock_sentinel_cls.call_args.kwargs["sentinel_kwargs"]
        assert sentinel_kwargs["password"] == SENTINEL_PASSWORD
        assert "username" not in sentinel_kwargs

    @pytest.mark.parametrize("factory", [get_redis_object, get_redis_object_for_lock])
    def test_master_for_without_username_is_unchanged(
        self, factory: SentinelFactory, sentinel_target_without_username: RedisTarget
    ) -> None:
        with patch("ai.backend.common.redis_helper.Sentinel") as mock_sentinel_cls:
            mock_sentinel_cls.return_value = MagicMock()
            factory(sentinel_target_without_username, name="test", db=0)
        master_kwargs = mock_sentinel_cls.return_value.master_for.call_args.kwargs
        assert master_kwargs["username"] is None
        assert master_kwargs["password"] == PASSWORD


class TestCreateValkeyClientCredentials:
    @pytest.mark.parametrize(
        ("username", "expected"),
        [(ACL_USERNAME, ACL_USERNAME), (None, None)],
    )
    async def test_server_credentials_username(
        self, username: str | None, expected: str | None
    ) -> None:
        target = ValkeyTarget(addr="127.0.0.1:6379", username=username, password=PASSWORD)
        with (
            patch("ai.backend.common.redis_helper.GlideClient.create", new_callable=AsyncMock),
            patch("ai.backend.common.redis_helper.ServerCredentials") as mock_cred,
        ):
            await create_valkey_client(target, name="test")
        mock_cred.assert_called_once_with(password=PASSWORD, username=expected)
