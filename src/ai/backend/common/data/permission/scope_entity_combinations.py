"""Valid RBAC scope-entity combinations based on BEP-1048/entity-edge-catalog.md.

This module is the single source of truth for which entity types are valid
under each scope type. It is used for:
- Frontend UI filtering (which entity types to show for a given scope)
- Server-side validation (reject invalid combinations)
"""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.data.permission.types import RBACElementType

VALID_SCOPE_ENTITY_COMBINATIONS: Mapping[RBACElementType, frozenset[RBACElementType]] = {
    RBACElementType.DOMAIN: frozenset({
        RBACElementType.RESOURCE_GROUP,
        RBACElementType.CONTAINER_REGISTRY,
        RBACElementType.USER,
        RBACElementType.PROJECT,
        RBACElementType.NETWORK,
        RBACElementType.STORAGE_HOST,
    }),
    RBACElementType.PROJECT: frozenset({
        RBACElementType.RESOURCE_GROUP,
        RBACElementType.CONTAINER_REGISTRY,
        RBACElementType.SESSION,
        RBACElementType.VFOLDER,
        RBACElementType.DEPLOYMENT,
        RBACElementType.NETWORK,
        RBACElementType.USER,
        RBACElementType.STORAGE_HOST,
    }),
    RBACElementType.USER: frozenset({
        RBACElementType.RESOURCE_GROUP,
        RBACElementType.SESSION,
        RBACElementType.VFOLDER,
        RBACElementType.DEPLOYMENT,
        RBACElementType.KEYPAIR,
    }),
    RBACElementType.RESOURCE_GROUP: frozenset({
        RBACElementType.AGENT,
        RBACElementType.USER_FAIR_SHARE,
    }),
    RBACElementType.AGENT: frozenset({
        RBACElementType.KERNEL,
    }),
    RBACElementType.SESSION: frozenset({
        RBACElementType.KERNEL,
    }),
    RBACElementType.MODEL_DEPLOYMENT: frozenset({
        RBACElementType.ROUTING,
        RBACElementType.SESSION,
    }),
    RBACElementType.CONTAINER_REGISTRY: frozenset({
        RBACElementType.IMAGE,
    }),
    RBACElementType.STORAGE_HOST: frozenset({
        RBACElementType.VFOLDER,
    }),
}
