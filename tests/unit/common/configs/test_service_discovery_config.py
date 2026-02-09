from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.configs.service_discovery import (
    ServiceDiscoveryConfig,
    ServiceEndpointConfig,
)
from ai.backend.common.types import ServiceDiscoveryType


class TestServiceEndpointConfig:
    """Tests for ServiceEndpointConfig."""

    def test_create_with_required_fields(self) -> None:
        config = ServiceEndpointConfig.model_validate({
            "role": "main",
            "scope": "public",
            "address": "127.0.0.1",
            "port": 8080,
            "protocol": "http",
        })
        assert config.role == "main"
        assert config.scope == "public"
        assert config.address == "127.0.0.1"
        assert config.port == 8080
        assert config.protocol == "http"
        assert config.metadata == {}

    def test_create_with_metadata(self) -> None:
        config = ServiceEndpointConfig.model_validate({
            "role": "health",
            "scope": "internal",
            "address": "10.0.0.1",
            "port": 9090,
            "protocol": "grpc",
            "metadata": {"weight": "100"},
        })
        assert config.metadata == {"weight": "100"}

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            ServiceEndpointConfig.model_validate({
                "role": "main",
                "scope": "public",
                # address is missing
                "port": 8080,
                "protocol": "http",
            })

    def test_kebab_case_alias(self) -> None:
        """Verify TOML-compatible kebab-case field aliases work."""
        config = ServiceEndpointConfig.model_validate({
            "role": "main",
            "scope": "public",
            "address": "127.0.0.1",
            "port": 8080,
            "protocol": "http",
        })
        assert config.role == "main"


class TestServiceDiscoveryConfig:
    """Tests for ServiceDiscoveryConfig."""

    def test_backward_compatible_minimal(self) -> None:
        """Existing configs with only 'type' should still work."""
        config = ServiceDiscoveryConfig.model_validate({"type": "redis"})
        assert config.type == ServiceDiscoveryType.REDIS
        assert config.instance_id is None
        assert config.service_group is None
        assert config.display_name is None
        assert config.extra_labels == {}
        assert config.endpoints == []

    def test_default_type(self) -> None:
        """Default config should use REDIS type."""
        config = ServiceDiscoveryConfig.model_validate({})
        assert config.type == ServiceDiscoveryType.REDIS

    def test_full_config(self) -> None:
        config = ServiceDiscoveryConfig.model_validate({
            "type": "redis",
            "instance-id": "manager-001",
            "service-group": "manager",
            "display-name": "Manager Instance 1",
            "extra-labels": {"region": "us-west-2", "zone": "a"},
            "endpoints": [
                {
                    "role": "main",
                    "scope": "public",
                    "address": "manager.example.com",
                    "port": 443,
                    "protocol": "https",
                },
                {
                    "role": "health",
                    "scope": "internal",
                    "address": "10.0.0.1",
                    "port": 9090,
                    "protocol": "http",
                },
            ],
        })
        assert config.instance_id == "manager-001"
        assert config.service_group == "manager"
        assert config.display_name == "Manager Instance 1"
        assert len(config.extra_labels) == 2
        assert len(config.endpoints) == 2
        assert config.endpoints[0].role == "main"
        assert config.endpoints[1].port == 9090

    def test_kebab_case_alias(self) -> None:
        """Verify TOML-compatible kebab-case aliases for new fields."""
        config = ServiceDiscoveryConfig.model_validate({
            "type": "redis",
            "instance-id": "mgr-001",
            "service-group": "manager",
            "display-name": "Manager 1",
            "extra-labels": {"env": "prod"},
        })
        assert config.instance_id == "mgr-001"
        assert config.service_group == "manager"
        assert config.display_name == "Manager 1"
        assert config.extra_labels == {"env": "prod"}

    def test_snake_case_field_names(self) -> None:
        """Verify snake_case field names also work (validate_by_name=True)."""
        config = ServiceDiscoveryConfig.model_validate({
            "type": "redis",
            "instance_id": "mgr-002",
            "service_group": "agent",
            "display_name": "Agent 1",
            "extra_labels": {"env": "dev"},
        })
        assert config.instance_id == "mgr-002"
        assert config.service_group == "agent"
