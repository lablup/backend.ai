"""Valid RBAC scope-entity combinations based on BEP-1048/entity-edge-catalog.md.

This module is the single source of truth for which entity types are valid
under each scope type. It is used for:
- Frontend UI filtering (which entity types to show for a given scope)
- Server-side validation (reject invalid combinations)
"""

from __future__ import annotations

from ai.backend.common.data.permission.types import RBACElementType

VALID_SCOPE_ENTITY_COMBINATIONS: dict[RBACElementType, set[RBACElementType]] = {
    RBACElementType.DOMAIN: {
        RBACElementType.RESOURCE_GROUP,
        RBACElementType.CONTAINER_REGISTRY,
        RBACElementType.USER,
        RBACElementType.PROJECT,
        RBACElementType.NETWORK,
        RBACElementType.STORAGE_HOST,
    },
    RBACElementType.PROJECT: {
        RBACElementType.RESOURCE_GROUP,
        RBACElementType.CONTAINER_REGISTRY,
        RBACElementType.SESSION,
        RBACElementType.VFOLDER,
        RBACElementType.DEPLOYMENT,
        RBACElementType.NETWORK,
        RBACElementType.USER,
        RBACElementType.STORAGE_HOST,
    },
    RBACElementType.USER: {
        RBACElementType.RESOURCE_GROUP,
        RBACElementType.SESSION,
        RBACElementType.VFOLDER,
        RBACElementType.DEPLOYMENT,
        RBACElementType.KEYPAIR,
    },
    RBACElementType.RESOURCE_GROUP: {
        RBACElementType.AGENT,
    },
    RBACElementType.AGENT: {
        RBACElementType.KERNEL,
    },
    RBACElementType.SESSION: {
        RBACElementType.KERNEL,
    },
    RBACElementType.MODEL_DEPLOYMENT: {
        RBACElementType.ROUTING,
        RBACElementType.SESSION,
    },
    RBACElementType.CONTAINER_REGISTRY: {
        RBACElementType.IMAGE,
    },
    RBACElementType.STORAGE_HOST: {
        RBACElementType.VFOLDER,
    },
}
