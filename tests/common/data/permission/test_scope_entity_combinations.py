"""Tests for RBAC scope-entity combination constants and validation."""

from __future__ import annotations

import pytest

from ai.backend.common.data.permission.scope_entity_combinations import (
    VALID_SCOPE_ENTITY_COMBINATIONS,
    VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION,
    is_valid_scope_entity_combination,
)
from ai.backend.common.data.permission.types import RBACElementType, RelationType


class TestValidScopeEntityCombinations:
    """Tests for the VALID_SCOPE_ENTITY_COMBINATIONS constant."""

    def test_domain_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.DOMAIN]
        assert RBACElementType.RESOURCE_GROUP in entities
        assert RBACElementType.CONTAINER_REGISTRY in entities
        assert RBACElementType.USER in entities
        assert RBACElementType.PROJECT in entities
        assert RBACElementType.NETWORK in entities

    def test_project_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.PROJECT]
        assert RBACElementType.RESOURCE_GROUP in entities
        assert RBACElementType.CONTAINER_REGISTRY in entities
        assert RBACElementType.SESSION in entities
        assert RBACElementType.VFOLDER in entities
        assert RBACElementType.DEPLOYMENT in entities
        assert RBACElementType.NETWORK in entities
        assert RBACElementType.USER in entities  # ref edge

    def test_user_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.USER]
        assert RBACElementType.RESOURCE_GROUP in entities
        assert RBACElementType.SESSION in entities
        assert RBACElementType.VFOLDER in entities
        assert RBACElementType.DEPLOYMENT in entities
        assert RBACElementType.KEYPAIR in entities

    def test_only_scope_types_are_keys(self) -> None:
        scope_types = {RBACElementType.DOMAIN, RBACElementType.PROJECT, RBACElementType.USER}
        assert set(VALID_SCOPE_ENTITY_COMBINATIONS.keys()) == scope_types


class TestValidScopeEntityCombinationsByRelation:
    """Tests for the VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION constant."""

    def test_auto_edges_domain(self) -> None:
        auto = VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION[RelationType.AUTO]
        entities = auto[RBACElementType.DOMAIN]
        assert RBACElementType.RESOURCE_GROUP in entities
        assert RBACElementType.CONTAINER_REGISTRY in entities
        assert RBACElementType.USER in entities
        assert RBACElementType.PROJECT in entities
        assert RBACElementType.NETWORK in entities

    def test_auto_edges_project(self) -> None:
        auto = VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION[RelationType.AUTO]
        entities = auto[RBACElementType.PROJECT]
        assert RBACElementType.RESOURCE_GROUP in entities
        assert RBACElementType.CONTAINER_REGISTRY in entities
        assert RBACElementType.SESSION in entities
        assert RBACElementType.VFOLDER in entities
        assert RBACElementType.DEPLOYMENT in entities
        assert RBACElementType.NETWORK in entities
        # User is ref-only, not auto, in Project scope
        assert RBACElementType.USER not in entities

    def test_auto_edges_user(self) -> None:
        auto = VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION[RelationType.AUTO]
        entities = auto[RBACElementType.USER]
        assert RBACElementType.RESOURCE_GROUP in entities
        assert RBACElementType.SESSION in entities
        assert RBACElementType.VFOLDER in entities
        assert RBACElementType.DEPLOYMENT in entities
        assert RBACElementType.KEYPAIR in entities

    def test_ref_edges_project_user(self) -> None:
        ref = VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION[RelationType.REF]
        entities = ref[RBACElementType.PROJECT]
        assert RBACElementType.USER in entities

    def test_ref_edges_no_domain(self) -> None:
        ref = VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION[RelationType.REF]
        assert RBACElementType.DOMAIN not in ref

    def test_ref_edges_no_user_scope(self) -> None:
        ref = VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION[RelationType.REF]
        assert RBACElementType.USER not in ref


class TestIsValidScopeEntityCombination:
    """Tests for the is_valid_scope_entity_combination helper."""

    @pytest.mark.parametrize(
        ("scope", "entity"),
        [
            (RBACElementType.DOMAIN, RBACElementType.RESOURCE_GROUP),
            (RBACElementType.DOMAIN, RBACElementType.CONTAINER_REGISTRY),
            (RBACElementType.DOMAIN, RBACElementType.USER),
            (RBACElementType.DOMAIN, RBACElementType.PROJECT),
            (RBACElementType.DOMAIN, RBACElementType.NETWORK),
            (RBACElementType.PROJECT, RBACElementType.RESOURCE_GROUP),
            (RBACElementType.PROJECT, RBACElementType.CONTAINER_REGISTRY),
            (RBACElementType.PROJECT, RBACElementType.SESSION),
            (RBACElementType.PROJECT, RBACElementType.VFOLDER),
            (RBACElementType.PROJECT, RBACElementType.DEPLOYMENT),
            (RBACElementType.PROJECT, RBACElementType.NETWORK),
            (RBACElementType.PROJECT, RBACElementType.USER),
            (RBACElementType.USER, RBACElementType.RESOURCE_GROUP),
            (RBACElementType.USER, RBACElementType.SESSION),
            (RBACElementType.USER, RBACElementType.VFOLDER),
            (RBACElementType.USER, RBACElementType.DEPLOYMENT),
            (RBACElementType.USER, RBACElementType.KEYPAIR),
        ],
    )
    def test_valid_combinations(self, scope: RBACElementType, entity: RBACElementType) -> None:
        assert is_valid_scope_entity_combination(scope, entity) is True

    @pytest.mark.parametrize(
        ("scope", "entity"),
        [
            # Domain does not contain Session or KeyPair directly
            (RBACElementType.DOMAIN, RBACElementType.SESSION),
            (RBACElementType.DOMAIN, RBACElementType.KEYPAIR),
            # Project does not contain KeyPair
            (RBACElementType.PROJECT, RBACElementType.KEYPAIR),
            # User does not contain Project or ContainerRegistry
            (RBACElementType.USER, RBACElementType.PROJECT),
            (RBACElementType.USER, RBACElementType.CONTAINER_REGISTRY),
            # Non-scope type used as scope
            (RBACElementType.SESSION, RBACElementType.VFOLDER),
            (RBACElementType.RESOURCE_GROUP, RBACElementType.USER),
        ],
    )
    def test_invalid_combinations(self, scope: RBACElementType, entity: RBACElementType) -> None:
        assert is_valid_scope_entity_combination(scope, entity) is False

    def test_with_auto_relation_type(self) -> None:
        # Domain → User is auto
        assert (
            is_valid_scope_entity_combination(
                RBACElementType.DOMAIN,
                RBACElementType.USER,
                relation_type=RelationType.AUTO,
            )
            is True
        )
        # Project → User is ref, not auto
        assert (
            is_valid_scope_entity_combination(
                RBACElementType.PROJECT,
                RBACElementType.USER,
                relation_type=RelationType.AUTO,
            )
            is False
        )

    def test_with_ref_relation_type(self) -> None:
        # Project → User is ref
        assert (
            is_valid_scope_entity_combination(
                RBACElementType.PROJECT,
                RBACElementType.USER,
                relation_type=RelationType.REF,
            )
            is True
        )
        # Domain → User is auto, not ref
        assert (
            is_valid_scope_entity_combination(
                RBACElementType.DOMAIN,
                RBACElementType.USER,
                relation_type=RelationType.REF,
            )
            is False
        )

    def test_without_relation_type_includes_both(self) -> None:
        # Project → User is valid (via ref edge) when relation_type is None
        assert (
            is_valid_scope_entity_combination(
                RBACElementType.PROJECT,
                RBACElementType.USER,
            )
            is True
        )
        # Project → Session is valid (via auto edge) when relation_type is None
        assert (
            is_valid_scope_entity_combination(
                RBACElementType.PROJECT,
                RBACElementType.SESSION,
            )
            is True
        )
