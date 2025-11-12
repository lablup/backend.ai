from __future__ import annotations

from datetime import datetime, timezone

from ai.backend.common.dto.internal.health import ComponentHealthStatus, HealthCheckResponse


def test_component_health_status_creation() -> None:
    """Test ComponentHealthStatus Pydantic model creation."""
    now = datetime.now(timezone.utc)
    status = ComponentHealthStatus(
        service_group="manager",
        component_id="postgres",
        is_healthy=True,
        last_checked_at=now,
        error_message=None,
    )

    assert status.service_group == "manager"
    assert status.component_id == "postgres"
    assert status.is_healthy is True
    assert status.last_checked_at == now
    assert status.error_message is None


def test_component_health_status_with_error() -> None:
    """Test ComponentHealthStatus with error message."""
    now = datetime.now(timezone.utc)
    error_msg = "Connection failed"

    status = ComponentHealthStatus(
        service_group="database",
        component_id="redis",
        is_healthy=False,
        last_checked_at=now,
        error_message=error_msg,
    )

    assert status.is_healthy is False
    assert status.error_message == error_msg


def test_component_health_status_serialization() -> None:
    """Test ComponentHealthStatus JSON serialization and deserialization."""
    now = datetime.now(timezone.utc)
    status = ComponentHealthStatus(
        service_group="manager",
        component_id="postgres",
        is_healthy=True,
        last_checked_at=now,
        error_message=None,
    )

    # Serialize to JSON
    json_data = status.model_dump_json()
    assert isinstance(json_data, str)

    # Deserialize from JSON
    restored = ComponentHealthStatus.model_validate_json(json_data)

    assert restored.service_group == status.service_group
    assert restored.component_id == status.component_id
    assert restored.is_healthy == status.is_healthy
    assert restored.error_message == status.error_message


def test_component_health_status_has_field_descriptions() -> None:
    """Test that ComponentHealthStatus has Field descriptions."""
    schema = ComponentHealthStatus.model_json_schema()

    assert "properties" in schema
    properties = schema["properties"]

    # Check that each field has a description
    assert "description" in properties["service_group"]
    assert "description" in properties["component_id"]
    assert "description" in properties["is_healthy"]
    assert "description" in properties["last_checked_at"]
    assert "description" in properties["error_message"]


def test_health_check_response_creation() -> None:
    """Test HealthCheckResponse Pydantic model creation."""
    now = datetime.now(timezone.utc)

    component1 = ComponentHealthStatus(
        service_group="manager",
        component_id="postgres",
        is_healthy=True,
        last_checked_at=now,
        error_message=None,
    )

    component2 = ComponentHealthStatus(
        service_group="database",
        component_id="redis",
        is_healthy=True,
        last_checked_at=now,
        error_message=None,
    )

    response = HealthCheckResponse(
        overall_healthy=True,
        components=[component1, component2],
        timestamp=now,
    )

    assert response.overall_healthy is True
    assert len(response.components) == 2
    assert response.timestamp == now


def test_health_check_response_with_unhealthy_components() -> None:
    """Test HealthCheckResponse with unhealthy components."""
    now = datetime.now(timezone.utc)

    component1 = ComponentHealthStatus(
        service_group="manager",
        component_id="postgres",
        is_healthy=True,
        last_checked_at=now,
        error_message=None,
    )

    component2 = ComponentHealthStatus(
        service_group="database",
        component_id="redis",
        is_healthy=False,
        last_checked_at=now,
        error_message="Connection timeout",
    )

    response = HealthCheckResponse(
        overall_healthy=False,
        components=[component1, component2],
        timestamp=now,
    )

    assert response.overall_healthy is False
    assert len(response.components) == 2


def test_health_check_response_serialization() -> None:
    """Test HealthCheckResponse JSON serialization and deserialization."""
    now = datetime.now(timezone.utc)

    component = ComponentHealthStatus(
        service_group="manager",
        component_id="postgres",
        is_healthy=True,
        last_checked_at=now,
        error_message=None,
    )

    response = HealthCheckResponse(
        overall_healthy=True,
        components=[component],
        timestamp=now,
    )

    # Serialize to JSON
    json_data = response.model_dump_json()
    assert isinstance(json_data, str)

    # Deserialize from JSON
    restored = HealthCheckResponse.model_validate_json(json_data)

    assert restored.overall_healthy == response.overall_healthy
    assert len(restored.components) == len(response.components)
    assert restored.components[0].service_group == component.service_group


def test_health_check_response_has_field_descriptions() -> None:
    """Test that HealthCheckResponse has Field descriptions."""
    schema = HealthCheckResponse.model_json_schema()

    assert "properties" in schema
    properties = schema["properties"]

    # Check that each field has a description
    assert "description" in properties["overall_healthy"]
    assert "description" in properties["components"]
    assert "description" in properties["timestamp"]


def test_health_check_response_empty_components() -> None:
    """Test HealthCheckResponse with no components."""
    now = datetime.now(timezone.utc)

    response = HealthCheckResponse(
        overall_healthy=True,
        components=[],
        timestamp=now,
    )

    assert response.overall_healthy is True
    assert len(response.components) == 0
    assert response.timestamp == now
