"""Valid RBAC scope-entity combinations based on BEP-1048/entity-edge-catalog.md.

This module is the single source of truth for which entity types are valid
under each scope type. It is used for:
- Frontend UI filtering (which entity types to show for a given scope)
- Server-side validation (reject invalid combinations)
"""

from __future__ import annotations

from ai.backend.common.data.permission.types import RBACElementType, RelationType

# ---------------------------------------------------------------------------
# Scope → Entity auto edges (N:N scope-accessibility mappings)
# ---------------------------------------------------------------------------
_AUTO_SCOPE_ENTITY: dict[RBACElementType, set[RBACElementType]] = {
    RBACElementType.DOMAIN: {
        RBACElementType.RESOURCE_GROUP,
        RBACElementType.CONTAINER_REGISTRY,
    },
    RBACElementType.PROJECT: {
        RBACElementType.RESOURCE_GROUP,
        RBACElementType.CONTAINER_REGISTRY,
    },
    RBACElementType.USER: {
        RBACElementType.RESOURCE_GROUP,
    },
}

# ---------------------------------------------------------------------------
# Scope → Member auto edges (1:N scope-composition)
# ---------------------------------------------------------------------------
_AUTO_SCOPE_MEMBER: dict[RBACElementType, set[RBACElementType]] = {
    RBACElementType.DOMAIN: {
        RBACElementType.USER,
        RBACElementType.PROJECT,
        RBACElementType.NETWORK,
    },
    RBACElementType.PROJECT: {
        RBACElementType.SESSION,
        RBACElementType.VFOLDER,
        RBACElementType.DEPLOYMENT,
        RBACElementType.NETWORK,
    },
    RBACElementType.USER: {
        RBACElementType.SESSION,
        RBACElementType.VFOLDER,
        RBACElementType.DEPLOYMENT,
        RBACElementType.KEYPAIR,
    },
}

# ---------------------------------------------------------------------------
# Scope → Entity ref edges (visibility-only mapping)
# ---------------------------------------------------------------------------
_REF_SCOPE_ENTITY: dict[RBACElementType, set[RBACElementType]] = {
    RBACElementType.PROJECT: {
        RBACElementType.USER,
    },
}

# ---------------------------------------------------------------------------
# Merged constants (auto ∪ ref per scope)
# ---------------------------------------------------------------------------

VALID_SCOPE_ENTITY_COMBINATIONS: dict[RBACElementType, set[RBACElementType]] = {}
"""All valid (scope, entity) pairs regardless of relation type.

The union of auto and ref edges for each scope type.
"""

for _src in (_AUTO_SCOPE_ENTITY, _AUTO_SCOPE_MEMBER, _REF_SCOPE_ENTITY):
    for _scope, _entities in _src.items():
        VALID_SCOPE_ENTITY_COMBINATIONS.setdefault(_scope, set()).update(_entities)

VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION: dict[
    RelationType, dict[RBACElementType, set[RBACElementType]]
] = {
    RelationType.AUTO: {},
    RelationType.REF: {},
}
"""Valid (scope, entity) pairs grouped by relation type."""

for _scope, _entities in _AUTO_SCOPE_ENTITY.items():
    VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION[RelationType.AUTO].setdefault(_scope, set()).update(
        _entities
    )
for _scope, _entities in _AUTO_SCOPE_MEMBER.items():
    VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION[RelationType.AUTO].setdefault(_scope, set()).update(
        _entities
    )
for _scope, _entities in _REF_SCOPE_ENTITY.items():
    VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION[RelationType.REF].setdefault(_scope, set()).update(
        _entities
    )

# Clean up module-level loop variables
del _src, _scope, _entities


def is_valid_scope_entity_combination(
    scope_type: RBACElementType,
    entity_type: RBACElementType,
    *,
    relation_type: RelationType | None = None,
) -> bool:
    """Check whether *entity_type* is valid under *scope_type*.

    Args:
        scope_type: The scope (parent) side of the edge.
        entity_type: The entity (child) side of the edge.
        relation_type: If given, restrict the check to edges of this relation
            type only. When ``None`` (the default), both ``auto`` and ``ref``
            edges are considered valid.

    Returns:
        ``True`` when the combination is catalogued in
        BEP-1048/entity-edge-catalog.md, ``False`` otherwise.
    """
    if relation_type is not None:
        source = VALID_SCOPE_ENTITY_COMBINATIONS_BY_RELATION.get(relation_type, {})
    else:
        source = VALID_SCOPE_ENTITY_COMBINATIONS
    return entity_type in source.get(scope_type, set())
