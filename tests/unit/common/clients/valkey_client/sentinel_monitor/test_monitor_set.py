from __future__ import annotations

import pytest

from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import (
    SentinelMonitorKey,
    SentinelMonitorSet,
)
from ai.backend.common.exception import ConfigurationError, ValkeySentinelMonitorNotFound
from ai.backend.common.types import HostPortPair, ValkeyTarget

SENTINELS = ["10.0.0.1:26379", "10.0.0.2:26379"]


def _sentinel_target(
    service_name: str = "mymaster",
    password: str | None = None,
    sentinel_password: str | None = None,
) -> ValkeyTarget:
    return ValkeyTarget(
        sentinel=list(SENTINELS),
        service_name=service_name,
        password=password,
        sentinel_password=sentinel_password,
    )


class TestSentinelMonitorKey:
    def test_standalone_target_has_no_key(self) -> None:
        assert SentinelMonitorKey.from_valkey_target(ValkeyTarget(addr="127.0.0.1:6379")) is None

    def test_parses_sentinel_addresses(self) -> None:
        key = SentinelMonitorKey.from_valkey_target(_sentinel_target())
        assert key is not None
        assert key.sentinel_addresses == (
            HostPortPair("10.0.0.1", 26379),
            HostPortPair("10.0.0.2", 26379),
        )

    def test_uses_sentinel_password_over_master_password(self) -> None:
        key = SentinelMonitorKey.from_valkey_target(
            _sentinel_target(password="master-pw", sentinel_password="sentinel-pw")
        )
        assert key is not None
        assert key.password == "sentinel-pw"

    def test_falls_back_to_master_password(self) -> None:
        key = SentinelMonitorKey.from_valkey_target(_sentinel_target(password="master-pw"))
        assert key is not None
        assert key.password == "master-pw"

    def test_rejects_sentinel_target_without_service_name(self) -> None:
        with pytest.raises(ConfigurationError):
            SentinelMonitorKey.from_valkey_target(ValkeyTarget(sentinel=list(SENTINELS)))


class TestSentinelMonitorSet:
    def test_targets_with_the_same_key_share_a_monitor(self) -> None:
        monitors = SentinelMonitorSet([_sentinel_target(), _sentinel_target()])

        first = monitors.monitor_for(_sentinel_target())
        second = monitors.monitor_for(_sentinel_target())

        assert first is not None
        assert first is second

    def test_each_service_gets_its_own_monitor(self) -> None:
        monitors = SentinelMonitorSet([_sentinel_target("main"), _sentinel_target("stream")])

        main = monitors.monitor_for(_sentinel_target("main"))
        stream = monitors.monitor_for(_sentinel_target("stream"))

        assert main is not None
        assert stream is not None
        assert main is not stream

    def test_standalone_target_has_no_monitor(self) -> None:
        monitors = SentinelMonitorSet([ValkeyTarget(addr="127.0.0.1:6379")])
        assert monitors.monitor_for(ValkeyTarget(addr="127.0.0.1:6379")) is None

    def test_unregistered_sentinel_target_raises(self) -> None:
        monitors = SentinelMonitorSet([_sentinel_target("main")])
        with pytest.raises(ValkeySentinelMonitorNotFound):
            monitors.monitor_for(_sentinel_target("other"))
