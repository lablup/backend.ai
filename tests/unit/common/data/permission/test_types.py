"""Tests for RBAC type conversions."""

from __future__ import annotations

import pytest

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.exception import RBACTypeConversionError

# Dynamically compute convertible members from enum value intersections.
# This avoids hard-coding and auto-covers new members added to any enum.
_entity_values = {e.value for e in EntityType}
_scope_values = {s.value for s in ScopeType}
_element_values = {e.value for e in RBACElementType}

_elements_with_entity = [e for e in RBACElementType if e.value in _entity_values]
_elements_without_entity = [e for e in RBACElementType if e.value not in _entity_values]
_entities_with_element = [e for e in EntityType if e.value in _element_values]
_entities_without_element = [e for e in EntityType if e.value not in _element_values]
_elements_with_scope = [e for e in RBACElementType if e.value in _scope_values]
_elements_without_scope = [e for e in RBACElementType if e.value not in _scope_values]


class TestRBACElementTypeToEntityType:
    """Tests for RBACElementType.to_entity_type() conversion."""

    @pytest.mark.parametrize("element_type", _elements_with_entity)
    def test_to_entity_type_round_trip(self, element_type: RBACElementType) -> None:
        """Test that to_entity_type() converts successfully and round-trips back."""
        entity_type = element_type.to_entity_type()
        assert isinstance(entity_type, EntityType)
        assert entity_type.value == element_type.value

        round_trip = entity_type.to_element()
        assert round_trip == element_type

    @pytest.mark.parametrize("element_type", _elements_without_entity)
    def test_element_without_entity_raises_error(self, element_type: RBACElementType) -> None:
        """Test that RBACElementType values without EntityType counterparts raise error."""
        with pytest.raises(RBACTypeConversionError, match="has no corresponding EntityType"):
            element_type.to_entity_type()


class TestEntityTypeToRBACElementType:
    """Tests for EntityType.to_element() conversion."""

    @pytest.mark.parametrize("entity_type", _entities_with_element)
    def test_to_element_conversion(self, entity_type: EntityType) -> None:
        """Test that to_element() converts EntityType to RBACElementType."""
        element_type = entity_type.to_element()
        assert isinstance(element_type, RBACElementType)
        assert element_type.value == entity_type.value

    @pytest.mark.parametrize("entity_type", _entities_without_element)
    def test_entity_without_element_raises_error(self, entity_type: EntityType) -> None:
        """Test that EntityType values without RBACElementType counterparts raise error."""
        with pytest.raises(RBACTypeConversionError, match="has no corresponding RBACElementType"):
            entity_type.to_element()


class TestRBACElementTypeToScopeType:
    """Tests for RBACElementType.to_scope_type() conversion."""

    @pytest.mark.parametrize("element_type", _elements_with_scope)
    def test_to_scope_type_round_trip(self, element_type: RBACElementType) -> None:
        """Test that to_scope_type() converts successfully and round-trips back."""
        scope_type = element_type.to_scope_type()
        assert isinstance(scope_type, ScopeType)
        assert scope_type.value == element_type.value

        round_trip = scope_type.to_element()
        assert round_trip == element_type

    @pytest.mark.parametrize("element_type", _elements_without_scope)
    def test_element_without_scope_raises_error(self, element_type: RBACElementType) -> None:
        """Test that RBACElementType values without ScopeType counterparts raise error."""
        with pytest.raises(RBACTypeConversionError, match="has no corresponding ScopeType"):
            element_type.to_scope_type()
