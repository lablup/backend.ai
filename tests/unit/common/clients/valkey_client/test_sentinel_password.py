from __future__ import annotations

from unittest.mock import patch

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
        assert sentinel_target.master_password == "master-pw"

    def test_falls_back_to_master_password_when_sentinel_password_is_none(self) -> None:
        valkey_target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-pw",
        )
        sentinel_target = ValkeySentinelTarget.from_valkey_target(valkey_target)

        assert sentinel_target.password == "master-pw"
        assert sentinel_target.master_password == "master-pw"


class TestValkeySentinelClientUsesResolvedPasswords:
    """Verify ValkeySentinelClient uses password for sentinel, master_password for GlideClient."""

    @pytest.fixture
    def target_with_separate_passwords(self) -> ValkeySentinelTarget:
        return ValkeySentinelTarget(
            sentinel_addresses=["127.0.0.1:26379"],
            service_name="mymaster",
            password="sentinel-secret",
            master_password="master-secret",
        )

    def test_sentinel_kwargs_uses_password(
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

        # password = sentinel password (resolved via from_valkey_target)
        assert operation_client._target.password == "sentinel-pw"
        assert monitor_client._target.password == "sentinel-pw"
        # master_password preserved for GlideClient credentials
        assert operation_client._target.master_password == "master-pw"
        assert monitor_client._target.master_password == "master-pw"

    def test_valkey_target_sentinel_password_defaults_to_none(self) -> None:
        target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            password="master-pw",
        )
        assert target.sentinel_password is None
