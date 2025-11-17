from __future__ import annotations

from datetime import datetime, timezone

from ai.backend.common.health_checker import (
    AGENT,
    APPPROXY,
    DATABASE,
    ETCD,
    MANAGER,
    REDIS,
    STORAGE_PROXY,
    ComponentHealthStatus,
    ComponentId,
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


def test_component_health_status_creation() -> None:
    """Test ComponentHealthStatus dataclass creation."""
    now = datetime.now(timezone.utc)
    status = ComponentHealthStatus(
        is_healthy=True,
        last_checked_at=now,
        error_message=None,
    )

    assert status.is_healthy is True
    assert status.last_checked_at == now
    assert status.error_message is None


def test_component_health_status_with_error() -> None:
    """Test ComponentHealthStatus with error message."""
    now = datetime.now(timezone.utc)
    error_msg = "Connection failed"
    status = ComponentHealthStatus(
        is_healthy=False,
        last_checked_at=now,
        error_message=error_msg,
    )

    assert status.is_healthy is False
    assert status.last_checked_at == now
    assert status.error_message == error_msg
