"""Tests for RBAC type conversions."""

from __future__ import annotations

import pytest

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.exception import RBACTypeConversionError


class TestRBACElementTypeToEntityType:
    """Tests for RBACElementType.to_entity_type() conversion."""

    @pytest.mark.parametrize(
        "element_type",
        [
            RBACElementType.DOMAIN,
            RBACElementType.PROJECT,
            RBACElementType.USER,
            RBACElementType.SESSION,
            RBACElementType.VFOLDER,
            RBACElementType.DEPLOYMENT,
            RBACElementType.MODEL_DEPLOYMENT,
            RBACElementType.KEYPAIR,
            RBACElementType.NOTIFICATION_CHANNEL,
            RBACElementType.NETWORK,
            RBACElementType.RESOURCE_GROUP,
            RBACElementType.CONTAINER_REGISTRY,
            RBACElementType.AGENT,
            RBACElementType.KERNEL,
            RBACElementType.ROUTING,
            RBACElementType.IMAGE,
            RBACElementType.ARTIFACT,
            RBACElementType.ARTIFACT_REGISTRY,
            RBACElementType.SESSION_TEMPLATE,
            RBACElementType.APP_CONFIG,
            RBACElementType.RESOURCE_PRESET,
            RBACElementType.ROLE,
            RBACElementType.AUDIT_LOG,
            RBACElementType.NOTIFICATION_RULE,
        ],
    )
    def test_to_entity_type_round_trip(self, element_type: RBACElementType) -> None:
        """Test that to_entity_type() converts successfully and round-trips back."""
        # Convert to EntityType
        entity_type = element_type.to_entity_type()
        assert isinstance(entity_type, EntityType)

        # Verify the value matches
        assert entity_type.value == element_type.value

        # Round-trip back to RBACElementType
        round_trip = entity_type.to_element()
        assert round_trip == element_type

    def test_kernel_conversion(self) -> None:
        """Test KERNEL conversion specifically (BA-5063)."""
        entity_type = RBACElementType.KERNEL.to_entity_type()
        assert entity_type == EntityType.KERNEL
        assert entity_type.value == "kernel"

        # Round-trip
        round_trip = entity_type.to_element()
        assert round_trip == RBACElementType.KERNEL

    def test_routing_conversion(self) -> None:
        """Test ROUTING conversion specifically (BA-5063)."""
        entity_type = RBACElementType.ROUTING.to_entity_type()
        assert entity_type == EntityType.ROUTING
        assert entity_type.value == "routing"

        # Round-trip
        round_trip = entity_type.to_element()
        assert round_trip == RBACElementType.ROUTING

    def test_element_without_entity_raises_error(self) -> None:
        """Test that RBACElementType values without EntityType counterparts raise error."""
        # EVENT_LOG is in RBACElementType but not in EntityType
        with pytest.raises(RBACTypeConversionError) as exc_info:
            RBACElementType.EVENT_LOG.to_entity_type()

        assert "has no corresponding EntityType" in str(exc_info.value)


class TestEntityTypeToRBACElementType:
    """Tests for EntityType.to_element() conversion."""

    @pytest.mark.parametrize(
        "entity_type",
        [
            EntityType.DOMAIN,
            EntityType.PROJECT,
            EntityType.USER,
            EntityType.SESSION,
            EntityType.VFOLDER,
            EntityType.IMAGE,
            EntityType.ARTIFACT,
            EntityType.ARTIFACT_REGISTRY,
            EntityType.APP_CONFIG,
            EntityType.NOTIFICATION_CHANNEL,
            EntityType.NOTIFICATION_RULE,
            EntityType.MODEL_DEPLOYMENT,
            EntityType.AGENT,
            EntityType.CONTAINER_REGISTRY,
            EntityType.DEPLOYMENT,
            EntityType.KERNEL,
            EntityType.KEYPAIR,
            EntityType.NETWORK,
            EntityType.RESOURCE_GROUP,
            EntityType.ROLE,
            EntityType.ROUTING,
            EntityType.SESSION_TEMPLATE,
        ],
    )
    def test_to_element_conversion(self, entity_type: EntityType) -> None:
        """Test that to_element() converts EntityType to RBACElementType."""
        element_type = entity_type.to_element()
        assert isinstance(element_type, RBACElementType)
        assert element_type.value == entity_type.value

    def test_entity_without_element_raises_error(self) -> None:
        """Test that EntityType values without RBACElementType counterparts raise error."""
        # AUTH is in EntityType but not in RBACElementType
        with pytest.raises(RBACTypeConversionError) as exc_info:
            EntityType.AUTH.to_element()

        assert "has no corresponding RBACElementType" in str(exc_info.value)


class TestRBACElementTypeToScopeType:
    """Tests for RBACElementType.to_scope_type() conversion."""

    @pytest.mark.parametrize(
        "element_type",
        [
            RBACElementType.DOMAIN,
            RBACElementType.PROJECT,
            RBACElementType.USER,
            RBACElementType.RESOURCE_GROUP,
            RBACElementType.CONTAINER_REGISTRY,
            RBACElementType.STORAGE_HOST,
            RBACElementType.SESSION,
            RBACElementType.DEPLOYMENT,
            RBACElementType.MODEL_DEPLOYMENT,
            RBACElementType.VFOLDER,
            RBACElementType.IMAGE,
            RBACElementType.ARTIFACT,
            RBACElementType.ARTIFACT_REVISION,
            RBACElementType.AGENT,
            RBACElementType.ROLE,
            RBACElementType.NOTIFICATION_CHANNEL,
            RBACElementType.ARTIFACT_REGISTRY,
        ],
    )
    def test_to_scope_type_round_trip(self, element_type: RBACElementType) -> None:
        """Test that to_scope_type() converts successfully and round-trips back."""
        scope_type = element_type.to_scope_type()
        assert isinstance(scope_type, ScopeType)
        assert scope_type.value == element_type.value

        # Round-trip back to RBACElementType
        round_trip = scope_type.to_element()
        assert round_trip == element_type

    def test_model_deployment_conversion(self) -> None:
        """Test MODEL_DEPLOYMENT scope conversion specifically."""
        scope_type = RBACElementType.MODEL_DEPLOYMENT.to_scope_type()
        assert scope_type == ScopeType.MODEL_DEPLOYMENT
        assert scope_type.value == "model_deployment"

        round_trip = scope_type.to_element()
        assert round_trip == RBACElementType.MODEL_DEPLOYMENT

    def test_agent_scope_conversion(self) -> None:
        """Test AGENT scope conversion specifically."""
        scope_type = RBACElementType.AGENT.to_scope_type()
        assert scope_type == ScopeType.AGENT
        assert scope_type.value == "agent"

        round_trip = scope_type.to_element()
        assert round_trip == RBACElementType.AGENT

    def test_element_without_scope_raises_error(self) -> None:
        """Test that RBACElementType values without ScopeType counterparts raise error."""
        with pytest.raises(RBACTypeConversionError) as exc_info:
            RBACElementType.EVENT_LOG.to_scope_type()

        assert "has no corresponding ScopeType" in str(exc_info.value)
