from ai.backend.manager.data.permission.types import OperationType


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
