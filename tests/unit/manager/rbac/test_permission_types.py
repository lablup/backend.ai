import pytest

from ai.backend.manager.data.permission.types import (
    ENTITY_GRAPH,
    ENTITY_TO_SCOPE_MAP,
    SCOPE_TO_ENTITY_MAP,
    EntityType,
    InvalidTypeConversionError,
    OperationType,
    RelationType,
    ScopeType,
    entity_type_to_scope_type,
    get_relation_type,
    scope_type_to_entity_type,
)


class TestOperationType:
    def test_owner_operations_contains_all(self) -> None:
        """Test that owner_operations contains all operation types."""
        owner_ops = OperationType.owner_operations()
        all_ops = set(OperationType)

        assert owner_ops == all_ops

        # Verify specific operations are included
        assert OperationType.CREATE in owner_ops
        assert OperationType.READ in owner_ops
        assert OperationType.UPDATE in owner_ops
        assert OperationType.SOFT_DELETE in owner_ops
        assert OperationType.HARD_DELETE in owner_ops
        assert OperationType.GRANT_ALL in owner_ops
        assert OperationType.GRANT_READ in owner_ops
        assert OperationType.GRANT_UPDATE in owner_ops
        assert OperationType.GRANT_SOFT_DELETE in owner_ops
        assert OperationType.GRANT_HARD_DELETE in owner_ops

    def test_admin_operations_contains_all(self) -> None:
        """Test that admin_operations contains all operation types."""
        admin_ops = OperationType.admin_operations()
        all_ops = set(OperationType)

        assert admin_ops == all_ops

        # Verify specific operations are included
        assert OperationType.CREATE in admin_ops
        assert OperationType.READ in admin_ops
        assert OperationType.UPDATE in admin_ops
        assert OperationType.SOFT_DELETE in admin_ops
        assert OperationType.HARD_DELETE in admin_ops
        assert OperationType.GRANT_ALL in admin_ops
        assert OperationType.GRANT_READ in admin_ops
        assert OperationType.GRANT_UPDATE in admin_ops
        assert OperationType.GRANT_SOFT_DELETE in admin_ops
        assert OperationType.GRANT_HARD_DELETE in admin_ops

    def test_member_operations_contains_only_read(self) -> None:
        """Test that member_operations contains only READ operation."""
        member_ops = OperationType.member_operations()

        assert len(member_ops) == 1
        assert OperationType.READ in member_ops

        # Verify other operations are NOT included
        assert OperationType.CREATE not in member_ops
        assert OperationType.UPDATE not in member_ops
        assert OperationType.SOFT_DELETE not in member_ops
        assert OperationType.HARD_DELETE not in member_ops
        assert OperationType.GRANT_ALL not in member_ops
        assert OperationType.GRANT_READ not in member_ops
        assert OperationType.GRANT_UPDATE not in member_ops
        assert OperationType.GRANT_SOFT_DELETE not in member_ops
        assert OperationType.GRANT_HARD_DELETE not in member_ops


class TestEntityType:
    def test_owner_accessible_entity_types_in_user(self) -> None:
        """Test that owner_accessible_entity_types_in_user contains resource types."""
        owner_accessible = EntityType.owner_accessible_entity_types_in_user()

        # Should contain all resource types
        assert EntityType.VFOLDER in owner_accessible
        assert EntityType.IMAGE in owner_accessible
        assert EntityType.SESSION in owner_accessible

        # Should NOT contain scope types
        assert EntityType.USER not in owner_accessible
        assert EntityType.PROJECT not in owner_accessible
        assert EntityType.DOMAIN not in owner_accessible

        # Verify it equals _resource_types()
        assert owner_accessible == EntityType._resource_types()

    def test_admin_accessible_entity_types_in_project(self) -> None:
        """Test that admin_accessible_entity_types_in_project contains resource types and USER."""
        admin_accessible = EntityType.admin_accessible_entity_types_in_project()

        # Should contain all resource types
        assert EntityType.VFOLDER in admin_accessible
        assert EntityType.IMAGE in admin_accessible
        assert EntityType.SESSION in admin_accessible

        # Should also contain USER
        assert EntityType.USER in admin_accessible

        # Should NOT contain PROJECT and DOMAIN
        assert EntityType.PROJECT not in admin_accessible
        assert EntityType.DOMAIN not in admin_accessible

        # Verify it equals _resource_types() + USER
        expected = {*EntityType._resource_types(), EntityType.USER}
        assert admin_accessible == expected

    def test_member_accessible_entity_types_in_project(self) -> None:
        """Test that member_accessible_entity_types_in_project contains resource types and USER."""
        member_accessible = EntityType.member_accessible_entity_types_in_project()

        # Should contain all resource types
        assert EntityType.VFOLDER in member_accessible
        assert EntityType.IMAGE in member_accessible
        assert EntityType.SESSION in member_accessible

        # Should also contain USER
        assert EntityType.USER in member_accessible

        # Should NOT contain PROJECT and DOMAIN
        assert EntityType.PROJECT not in member_accessible
        assert EntityType.DOMAIN not in member_accessible

        # Verify it equals _resource_types() + USER
        expected = {*EntityType._resource_types(), EntityType.USER}
        assert member_accessible == expected

    def test_rbac_entity_types_are_categorized(self) -> None:
        """Test that RBAC scope and resource types have no overlap and cover the original 12 types."""
        scope_types = EntityType._scope_types()
        resource_types = EntityType._resource_types()

        # Verify no overlap between scope and resource types
        overlap = scope_types.intersection(resource_types)
        assert len(overlap) == 0, f"Entity types found in both scope and resource: {overlap}"

        # Verify scope types are exactly 3
        assert scope_types == {EntityType.USER, EntityType.PROJECT, EntityType.DOMAIN}

        # Verify resource types are exactly 9
        assert resource_types == {
            EntityType.VFOLDER,
            EntityType.IMAGE,
            EntityType.SESSION,
            EntityType.ARTIFACT,
            EntityType.ARTIFACT_REGISTRY,
            EntityType.APP_CONFIG,
            EntityType.NOTIFICATION_CHANNEL,
            EntityType.NOTIFICATION_RULE,
            EntityType.MODEL_DEPLOYMENT,
        }


class TestEntityGraph:
    def test_all_entity_types_are_graph_keys(self) -> None:
        """Every EntityType value must be a key in ENTITY_GRAPH."""
        for entity_type in EntityType:
            assert entity_type in ENTITY_GRAPH, f"Missing graph key: {entity_type}"

    def test_all_children_are_valid_entity_types(self) -> None:
        all_entity_types = set(EntityType)
        for parent, children in ENTITY_GRAPH.items():
            assert parent in all_entity_types, f"Invalid parent: {parent}"
            for child in children:
                assert child in all_entity_types, f"Invalid child: {child}"

    def test_no_self_referencing_edges(self) -> None:
        for parent, children in ENTITY_GRAPH.items():
            assert parent not in children, f"Self-referencing edge: {parent}"

    def test_known_parent_child_lookups(self) -> None:
        assert ENTITY_GRAPH[EntityType.SESSION][EntityType.SESSION_KERNEL] == RelationType.AUTO
        assert ENTITY_GRAPH[EntityType.SESSION][EntityType.AGENT] == RelationType.REF
        assert ENTITY_GRAPH[EntityType.CONTAINER_REGISTRY][EntityType.IMAGE] == RelationType.AUTO
        assert ENTITY_GRAPH[EntityType.PROJECT][EntityType.SESSION] == RelationType.AUTO

    def test_leaf_nodes_have_empty_children(self) -> None:
        assert ENTITY_GRAPH[EntityType.AUTH] == {}
        assert ENTITY_GRAPH[EntityType.AUDIT_LOG] == {}
        assert ENTITY_GRAPH[EntityType.IMAGE_ALIAS] == {}

    def test_get_relation_type_known_edges(self) -> None:
        assert get_relation_type(EntityType.SESSION, EntityType.SESSION_KERNEL) == RelationType.AUTO
        assert get_relation_type(EntityType.SESSION, EntityType.AGENT) == RelationType.REF
        assert (
            get_relation_type(EntityType.CONTAINER_REGISTRY, EntityType.IMAGE) == RelationType.AUTO
        )

    def test_get_relation_type_unknown_edge_returns_none(self) -> None:
        assert get_relation_type(EntityType.SESSION, EntityType.DOMAIN) is None
        assert get_relation_type(EntityType.IMAGE, EntityType.SESSION) is None

    def test_every_edge_has_distinct_parent_and_child(self) -> None:
        for parent, children in ENTITY_GRAPH.items():
            for child in children:
                assert parent != child, f"Self-referencing edge: {parent}"


class TestScopeEntityConverter:
    def test_scope_type_to_entity_type_valid_mappings(self) -> None:
        assert scope_type_to_entity_type(ScopeType.DOMAIN) == EntityType.DOMAIN
        assert scope_type_to_entity_type(ScopeType.PROJECT) == EntityType.PROJECT
        assert scope_type_to_entity_type(ScopeType.USER) == EntityType.USER
        assert scope_type_to_entity_type(ScopeType.RESOURCE_GROUP) == EntityType.RESOURCE_GROUP
        assert (
            scope_type_to_entity_type(ScopeType.CONTAINER_REGISTRY) == EntityType.CONTAINER_REGISTRY
        )
        assert (
            scope_type_to_entity_type(ScopeType.ARTIFACT_REGISTRY) == EntityType.ARTIFACT_REGISTRY
        )
        assert scope_type_to_entity_type(ScopeType.STORAGE_HOST) == EntityType.STORAGE_HOST
        assert scope_type_to_entity_type(ScopeType.SESSION) == EntityType.SESSION
        assert scope_type_to_entity_type(ScopeType.DEPLOYMENT) == EntityType.DEPLOYMENT
        assert scope_type_to_entity_type(ScopeType.VFOLDER) == EntityType.VFOLDER
        assert scope_type_to_entity_type(ScopeType.IMAGE) == EntityType.IMAGE
        assert scope_type_to_entity_type(ScopeType.ARTIFACT) == EntityType.ARTIFACT
        assert (
            scope_type_to_entity_type(ScopeType.ARTIFACT_REVISION) == EntityType.ARTIFACT_REVISION
        )
        assert scope_type_to_entity_type(ScopeType.ROLE) == EntityType.ROLE

    def test_scope_type_to_entity_type_global_raises(self) -> None:
        with pytest.raises(InvalidTypeConversionError):
            scope_type_to_entity_type(ScopeType.GLOBAL)

    def test_entity_type_to_scope_type_valid_mappings(self) -> None:
        assert entity_type_to_scope_type(EntityType.DOMAIN) == ScopeType.DOMAIN
        assert entity_type_to_scope_type(EntityType.PROJECT) == ScopeType.PROJECT
        assert entity_type_to_scope_type(EntityType.USER) == ScopeType.USER
        assert entity_type_to_scope_type(EntityType.RESOURCE_GROUP) == ScopeType.RESOURCE_GROUP
        assert entity_type_to_scope_type(EntityType.SESSION) == ScopeType.SESSION
        assert entity_type_to_scope_type(EntityType.STORAGE_HOST) == ScopeType.STORAGE_HOST

    def test_entity_type_to_scope_type_unmapped_raises(self) -> None:
        with pytest.raises(InvalidTypeConversionError):
            entity_type_to_scope_type(EntityType.AUTH)

    def test_scope_to_entity_map_excludes_global(self) -> None:
        assert ScopeType.GLOBAL not in SCOPE_TO_ENTITY_MAP
        assert len(SCOPE_TO_ENTITY_MAP) == len(ScopeType) - 1

    def test_entity_to_scope_map_is_inverse(self) -> None:
        for scope_type, entity_type in SCOPE_TO_ENTITY_MAP.items():
            assert ENTITY_TO_SCOPE_MAP[entity_type] == scope_type

    def test_roundtrip_scope_to_entity_to_scope(self) -> None:
        for scope_type in ScopeType:
            if scope_type == ScopeType.GLOBAL:
                continue
            entity_type = scope_type_to_entity_type(scope_type)
            assert entity_type_to_scope_type(entity_type) == scope_type
