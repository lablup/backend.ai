from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ai.backend.common.health_checker import (
    AGENT,
    APPPROXY,
    DATABASE,
    ETCD,
    MANAGER,
    REDIS,
    STORAGE_PROXY,
    ComponentId,
    HealthCheckKey,
    HealthCheckStatus,
    ServiceGroup,
)


def test_service_group_newtype() -> None:
    """Test ServiceGroup NewType creation."""
    custom_group = ServiceGroup("custom-service")
    assert custom_group == "custom-service"


def test_built_in_service_groups() -> None:
    """Test built-in service group constants."""
    assert MANAGER == "manager"
    assert AGENT == "agent"
    assert STORAGE_PROXY == "storage-proxy"
    assert APPPROXY == "appproxy"
    assert DATABASE == "database"
    assert ETCD == "etcd"
    assert REDIS == "redis"


def test_component_id_newtype() -> None:
    """Test ComponentId NewType creation."""
    component_id = ComponentId("postgres")
    assert component_id == "postgres"


def test_health_check_key_creation() -> None:
    """Test HealthCheckKey frozen dataclass creation."""
    key = HealthCheckKey(
        service_group=MANAGER,
        component_id=ComponentId("postgres"),
    )
    assert key.service_group == MANAGER
    assert key.component_id == ComponentId("postgres")


def test_health_check_key_hashable() -> None:
    """Test that HealthCheckKey is hashable and can be used as dict key."""
    key1 = HealthCheckKey(MANAGER, ComponentId("redis"))
    key2 = HealthCheckKey(MANAGER, ComponentId("redis"))
    key3 = HealthCheckKey(AGENT, ComponentId("redis"))

    # Same keys should have same hash
    assert key1 == key2
    assert hash(key1) == hash(key2)

    # Different keys should not be equal
    assert key1 != key3

    # Can be used as dict key
    test_dict: dict[HealthCheckKey, str] = {
        key1: "value1",
        key3: "value2",
    }
    assert test_dict[key1] == "value1"
    assert test_dict[key3] == "value2"


def test_health_check_key_immutable() -> None:
    """Test that HealthCheckKey is immutable (frozen dataclass)."""
    key = HealthCheckKey(
        service_group=MANAGER,
        component_id=ComponentId("postgres"),
    )

    with pytest.raises(AttributeError):
        key.service_group = AGENT  # type: ignore


def test_health_check_status_creation() -> None:
    """Test HealthCheckStatus dataclass creation."""
    now = datetime.now(timezone.utc)
    status = HealthCheckStatus(
        is_healthy=True,
        last_checked_at=now,
        error_message=None,
    )

    assert status.is_healthy is True
    assert status.last_checked_at == now
    assert status.error_message is None


def test_health_check_status_with_error() -> None:
    """Test HealthCheckStatus with error message."""
    now = datetime.now(timezone.utc)
    error_msg = "Connection failed"
    status = HealthCheckStatus(
        is_healthy=False,
        last_checked_at=now,
        error_message=error_msg,
    )

    assert status.is_healthy is False
    assert status.last_checked_at == now
    assert status.error_message == error_msg
