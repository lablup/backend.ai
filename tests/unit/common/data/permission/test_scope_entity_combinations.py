"""Tests for RBAC scope-entity combination constants."""

from __future__ import annotations

import pytest

from ai.backend.common.data.permission.scope_entity_combinations import (
    VALID_SCOPE_ENTITY_COMBINATIONS,
)
from ai.backend.common.data.permission.types import RBACElementType


class TestValidScopeEntityCombinations:
    """Tests for the VALID_SCOPE_ENTITY_COMBINATIONS constant."""

    def test_domain_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.DOMAIN]
        assert entities == {
            RBACElementType.RESOURCE_GROUP,
            RBACElementType.CONTAINER_REGISTRY,
            RBACElementType.USER,
            RBACElementType.PROJECT,
            RBACElementType.NETWORK,
            RBACElementType.STORAGE_HOST,
        }

    def test_project_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.PROJECT]
        assert entities == {
            RBACElementType.RESOURCE_GROUP,
            RBACElementType.CONTAINER_REGISTRY,
            RBACElementType.SESSION,
            RBACElementType.VFOLDER,
            RBACElementType.DEPLOYMENT,
            RBACElementType.NETWORK,
            RBACElementType.USER,
            RBACElementType.STORAGE_HOST,
        }

    def test_user_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.USER]
        assert entities == {
            RBACElementType.RESOURCE_GROUP,
            RBACElementType.SESSION,
            RBACElementType.VFOLDER,
            RBACElementType.DEPLOYMENT,
            RBACElementType.KEYPAIR,
        }

    def test_resource_group_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.RESOURCE_GROUP]
        assert entities == {
            RBACElementType.AGENT,
            RBACElementType.USER_FAIR_SHARE,
        }

    def test_agent_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.AGENT]
        assert entities == {
            RBACElementType.KERNEL,
        }

    def test_session_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.SESSION]
        assert entities == {
            RBACElementType.KERNEL,
        }

    def test_model_deployment_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.MODEL_DEPLOYMENT]
        assert entities == {
            RBACElementType.ROUTING,
            RBACElementType.SESSION,
        }

    def test_container_registry_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.CONTAINER_REGISTRY]
        assert entities == {
            RBACElementType.IMAGE,
        }

    def test_storage_host_scope_entities(self) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.STORAGE_HOST]
        assert entities == {
            RBACElementType.VFOLDER,
        }

    def test_scope_keys(self) -> None:
        expected_scopes = {
            RBACElementType.DOMAIN,
            RBACElementType.PROJECT,
            RBACElementType.USER,
            RBACElementType.RESOURCE_GROUP,
            RBACElementType.AGENT,
            RBACElementType.SESSION,
            RBACElementType.MODEL_DEPLOYMENT,
            RBACElementType.CONTAINER_REGISTRY,
            RBACElementType.STORAGE_HOST,
        }
        assert set(VALID_SCOPE_ENTITY_COMBINATIONS.keys()) == expected_scopes

    @pytest.mark.parametrize(
        ("scope", "entity"),
        [
            (RBACElementType.DOMAIN, RBACElementType.SESSION),
            (RBACElementType.DOMAIN, RBACElementType.KEYPAIR),
            (RBACElementType.PROJECT, RBACElementType.KEYPAIR),
            (RBACElementType.USER, RBACElementType.PROJECT),
            (RBACElementType.USER, RBACElementType.CONTAINER_REGISTRY),
            (RBACElementType.SESSION, RBACElementType.VFOLDER),
            (RBACElementType.SESSION, RBACElementType.SESSION),
        ],
    )
    def test_invalid_combinations(self, scope: RBACElementType, entity: RBACElementType) -> None:
        entities = VALID_SCOPE_ENTITY_COMBINATIONS.get(scope, frozenset())
        assert entity not in entities
