from __future__ import annotations

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.query import StringFilter, StringFilterMode
from ai.backend.common.dto.manager.user import (
    OrderDirection,
    SearchUsersRequest,
    SearchUsersResponse,
    UserFilter,
    UserOrder,
    UserOrderField,
    UserRole,
    UserStatus,
)

from .conftest import UserFactory


class TestUserSearch:
    """Tests for user search operations (component-level)."""

    async def test_s1_search_all_users_no_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-1: Search all users (no filter) → returns paginated list."""
        # Create a few test users to ensure non-empty result
        await user_factory()
        await user_factory()
        await user_factory()

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=None,
                limit=50,
                offset=0,
            )
        )

        assert isinstance(result, SearchUsersResponse)
        assert len(result.items) >= 3
        assert result.pagination.total >= 3

    async def test_s2_search_with_email_filter_contains(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-2: Search with email filter (contains) → only matching users returned."""
        # Create users with distinct email patterns
        user1 = await user_factory(email="search-test-alpha@test.local")
        user2 = await user_factory(email="search-test-beta@test.local")
        await user_factory(email="different@test.local")

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(
                        mode=StringFilterMode.CONTAINS,
                        value="search-test",
                    )
                ),
                limit=50,
            )
        )

        assert len(result.items) >= 2
        found_emails = {user.email for user in result.items}
        assert user1.user.email in found_emails
        assert user2.user.email in found_emails
        assert "different@test.local" not in found_emails

    async def test_s3_search_with_username_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-3: Search with username filter → only matching users returned."""
        target_user = await user_factory(username="specific-username-xyz")
        await user_factory(username="other-username-abc")

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    username=StringFilter(
                        mode=StringFilterMode.EXACT,
                        value="specific-username-xyz",
                    )
                ),
                limit=50,
            )
        )

        assert len(result.items) == 1
        assert result.items[0].username == target_user.user.username

    async def test_s4_search_with_status_filter_active(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-4: Search with status filter (ACTIVE) → filtered results."""
        active_user = await user_factory(status=UserStatus.ACTIVE)
        await user_factory(status=UserStatus.INACTIVE)

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(status=[UserStatus.ACTIVE]),
                limit=50,
            )
        )

        assert len(result.items) >= 1
        user_ids = {user.id for user in result.items}
        assert active_user.user.id in user_ids
        # Verify all returned users are ACTIVE
        assert all(user.status == UserStatus.ACTIVE for user in result.items)

    async def test_s5_search_with_status_filter_inactive(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-5: Search with status filter (INACTIVE) → filtered results."""
        await user_factory(status=UserStatus.ACTIVE)
        inactive_user = await user_factory(status=UserStatus.INACTIVE)

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(status=[UserStatus.INACTIVE]),
                limit=50,
            )
        )

        assert len(result.items) >= 1
        user_ids = {user.id for user in result.items}
        assert inactive_user.user.id in user_ids
        assert all(user.status == UserStatus.INACTIVE for user in result.items)

    async def test_s6_search_with_role_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-6: Search with role filter → filtered results."""
        user_role = await user_factory(role=UserRole.USER)
        await user_factory(role=UserRole.ADMIN)

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(role=[UserRole.USER]),
                limit=50,
            )
        )

        assert len(result.items) >= 1
        user_ids = {user.id for user in result.items}
        assert user_role.user.id in user_ids
        assert all(user.role == UserRole.USER for user in result.items)

    async def test_s7_search_with_pagination_offset_limit(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-7: Search with pagination (offset, limit) → correct page returned."""
        # Create multiple users to test pagination
        for _ in range(5):
            await user_factory()

        # Get first page
        page1 = await admin_registry.user.search(SearchUsersRequest(limit=2, offset=0))
        assert len(page1.items) == 2

        # Get second page
        page2 = await admin_registry.user.search(SearchUsersRequest(limit=2, offset=2))
        assert len(page2.items) == 2

        # Verify pages are different
        page1_ids = {user.id for user in page1.items}
        page2_ids = {user.id for user in page2.items}
        assert page1_ids.isdisjoint(page2_ids), "Pages should not overlap"

    async def test_s8_search_with_sorting_email_asc(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-8: Search with sorting (email ASC) → correctly ordered."""
        await user_factory(email="alpha@test.local")
        await user_factory(email="beta@test.local")
        await user_factory(email="gamma@test.local")

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(
                        mode=StringFilterMode.CONTAINS,
                        value="@test.local",
                    )
                ),
                order=[UserOrder(field=UserOrderField.EMAIL, direction=OrderDirection.ASC)],
                limit=50,
            )
        )

        # Verify results are sorted ascending by email
        emails = [user.email for user in result.items if "@test.local" in user.email]
        assert emails == sorted(emails)

    async def test_s9_search_with_sorting_email_desc(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-9: Search with sorting (email DESC) → correctly ordered."""
        await user_factory(email="alpha@test.local")
        await user_factory(email="beta@test.local")
        await user_factory(email="gamma@test.local")

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(
                        mode=StringFilterMode.CONTAINS,
                        value="@test.local",
                    )
                ),
                order=[UserOrder(field=UserOrderField.EMAIL, direction=OrderDirection.DESC)],
                limit=50,
            )
        )

        # Verify results are sorted descending by email
        emails = [user.email for user in result.items if "@test.local" in user.email]
        assert emails == sorted(emails, reverse=True)

    async def test_s10_search_with_compound_filters(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-10: Search with compound filters → intersection of conditions."""
        # Create user matching all conditions
        target = await user_factory(
            email="compound-test@test.local",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )
        # Create users matching only some conditions
        await user_factory(email="compound-test-2@test.local", status=UserStatus.INACTIVE)
        await user_factory(email="other@test.local", status=UserStatus.ACTIVE)

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(
                        mode=StringFilterMode.CONTAINS,
                        value="compound-test",
                    ),
                    status=[UserStatus.ACTIVE],
                    role=[UserRole.USER],
                ),
                limit=50,
            )
        )

        assert len(result.items) >= 1
        user_ids = {user.id for user in result.items}
        assert target.user.id in user_ids
        # Verify all conditions are met
        for user in result.items:
            assert "compound-test" in user.email
            assert user.status == UserStatus.ACTIVE
            assert user.role == UserRole.USER

    async def test_s11_search_empty_result(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-11: Empty result search → total=0, empty items."""
        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(
                        mode=StringFilterMode.EXACT,
                        value="nonexistent-user-email-xyz@test.local",
                    )
                ),
                limit=50,
            )
        )

        assert len(result.items) == 0
        assert result.pagination.total == 0


class TestUserBulkOperations:
    """Tests for user bulk operations (component-level).

    Note: Bulk operations are currently only exposed via GraphQL API,
    not REST API v2. These tests are placeholders for when the REST API
    v2 endpoints are implemented.
    """

    @pytest.mark.skip(reason="Bulk operations not yet implemented in REST API v2")
    async def test_s1_bulk_create_all_success(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-1: Bulk create all success → all users created, correct count."""
        pytest.skip("Bulk create not yet available in UserClient")

    @pytest.mark.skip(reason="Bulk operations not yet implemented in REST API v2")
    async def test_s2_bulk_create_partial_failure_duplicate_email(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-2: Bulk create partial failure (duplicate email) → success + failure lists with indices."""
        pytest.skip("Bulk create not yet available in UserClient")

    @pytest.mark.skip(reason="Bulk operations not yet implemented in REST API v2")
    async def test_s3_bulk_create_empty_list(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-3: Bulk create empty list → empty result (no error)."""
        pytest.skip("Bulk create not yet available in UserClient")

    @pytest.mark.skip(reason="Bulk operations not yet implemented in REST API v2")
    async def test_s4_bulk_modify_all_success(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-4: Bulk modify all success → all users updated."""
        pytest.skip("Bulk modify not yet available in UserClient")

    @pytest.mark.skip(reason="Bulk operations not yet implemented in REST API v2")
    async def test_s5_bulk_modify_partial_failure_nonexistent_user(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-5: Bulk modify partial failure (non-existent user) → success + failure with indices."""
        pytest.skip("Bulk modify not yet available in UserClient")

    @pytest.mark.skip(reason="Bulk operations not yet implemented in REST API v2")
    async def test_s6_bulk_purge_partial_failure_vfolder_mount_blocking(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-6: Bulk purge partial failure (vfolder mount blocking) → success + failure with indices."""
        pytest.skip("Bulk purge not yet available in UserClient")

    @pytest.mark.skip(reason="Bulk operations not yet implemented in REST API v2")
    async def test_s7_failure_index_tracking(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-7: Failure index tracking → each failure has correct index and error message."""
        pytest.skip("Bulk operations not yet available in UserClient")
