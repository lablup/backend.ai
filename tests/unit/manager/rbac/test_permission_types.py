from ai.backend.manager.data.permission.types import EntityType, OperationType


class TestOperationType:
    def test_owner_operations_contains_all(self):
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

    def test_admin_operations_contains_all(self):
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

    def test_member_operations_contains_only_read(self):
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
    def test_owner_accessible_entity_types_in_user(self):
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

    def test_admin_accessible_entity_types_in_project(self):
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

    def test_member_accessible_entity_types_in_project(self):
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

    def test_all_entity_types_are_categorized(self):
        """Test that all EntityType values are in either _scope_types or _resource_types."""
        all_entity_types = set(EntityType)
        scope_types = EntityType._scope_types()
        resource_types = EntityType._resource_types()

        # All entity types should be in either scope or resource types
        categorized_types = scope_types.union(resource_types)
        uncategorized = all_entity_types - categorized_types

        assert len(uncategorized) == 0, f"Uncategorized entity types found: {uncategorized}"

        # Verify no overlap between scope and resource types
        overlap = scope_types.intersection(resource_types)
        assert len(overlap) == 0, f"Entity types found in both scope and resource: {overlap}"

        # Verify all types are accounted for
        assert all_entity_types == categorized_types
