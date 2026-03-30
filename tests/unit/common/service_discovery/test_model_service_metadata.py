import uuid

import pytest

from ai.backend.common.service_discovery import (
    MODEL_SERVICE_GROUP,
    ModelServiceMetadata,
)


def test_model_service_metadata_to_service_metadata() -> None:
    """Test basic conversion from ModelServiceMetadata to ServiceMetadata."""
    route_id = uuid.uuid4()
    metadata = ModelServiceMetadata(
        route_id=route_id,
        model_service_name="llama-70b-prod-0",
        host="10.0.1.50",
        port=8080,
    )

    service_meta = metadata.to_service_metadata()

    assert service_meta.id == route_id
    assert service_meta.display_name == "llama-70b-prod-0"
    assert service_meta.service_group == MODEL_SERVICE_GROUP
    assert service_meta.endpoint.address == "10.0.1.50"
    assert service_meta.endpoint.port == 8080
    assert service_meta.endpoint.protocol == "http"
    assert service_meta.endpoint.prometheus_address == "10.0.1.50:8080"


def test_model_service_metadata_custom_metrics_path() -> None:
    """Test prometheus_address contains only host:port (no metrics path)."""
    metadata = ModelServiceMetadata(
        route_id=uuid.uuid4(),
        model_service_name="test-service",
        host="192.168.1.100",
        port=9090,
        metrics_path="/stats",
    )

    service_meta = metadata.to_service_metadata()

    # prometheus_address should only contain host:port
    assert service_meta.endpoint.prometheus_address == "192.168.1.100:9090"


def test_model_service_metadata_labels_auto_added() -> None:
    """Test route_id and model_service_name are automatically added to labels."""
    route_id = uuid.uuid4()
    metadata = ModelServiceMetadata(
        route_id=route_id,
        model_service_name="vllm-service-0",
        host="10.0.1.50",
        port=8080,
        labels={
            "deployment_name": "vllm-prod",
            "runtime_variant": "vllm",
        },
    )

    service_meta = metadata.to_service_metadata()

    assert "route_id" in service_meta.labels
    assert service_meta.labels["route_id"] == str(route_id)
    assert "model_service_name" in service_meta.labels
    assert service_meta.labels["model_service_name"] == "vllm-service-0"
    # User-provided labels should also be present
    assert service_meta.labels["deployment_name"] == "vllm-prod"
    assert service_meta.labels["runtime_variant"] == "vllm"


def test_model_service_metadata_labels_override() -> None:
    """Test that auto-added labels override user-provided ones."""
    route_id = uuid.uuid4()
    metadata = ModelServiceMetadata(
        route_id=route_id,
        model_service_name="correct-name",
        host="10.0.1.50",
        port=8080,
        labels={
            "route_id": "wrong-id",  # This should be overridden
            "model_service_name": "wrong-name",  # This should be overridden
            "custom_label": "custom_value",
        },
    )

    service_meta = metadata.to_service_metadata()

    # Auto-added labels should override user-provided ones
    assert service_meta.labels["route_id"] == str(route_id)
    assert service_meta.labels["model_service_name"] == "correct-name"
    # Custom label should remain
    assert service_meta.labels["custom_label"] == "custom_value"


def test_model_service_metadata_empty_labels() -> None:
    """Test that conversion works with no user-provided labels."""
    route_id = uuid.uuid4()
    metadata = ModelServiceMetadata(
        route_id=route_id,
        model_service_name="simple-service",
        host="127.0.0.1",
        port=8080,
    )

    service_meta = metadata.to_service_metadata()

    # Should only have auto-added labels
    assert len(service_meta.labels) == 2
    assert service_meta.labels["route_id"] == str(route_id)
    assert service_meta.labels["model_service_name"] == "simple-service"


def test_model_service_metadata_port_validation() -> None:
    """Test that invalid port numbers are rejected."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        ModelServiceMetadata(
            route_id=uuid.uuid4(),
            model_service_name="test",
            host="10.0.1.50",
            port=0,  # Invalid: too low
        )

    with pytest.raises(Exception):  # Pydantic ValidationError
        ModelServiceMetadata(
            route_id=uuid.uuid4(),
            model_service_name="test",
            host="10.0.1.50",
            port=65536,  # Invalid: too high
        )
