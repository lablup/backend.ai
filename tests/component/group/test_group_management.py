"""Component tests for group management operations.

Tests for:
- Group delete (soft delete)
- Group purge (hard delete with validation)
- Project search (filters, pagination, sorting)
- Usage statistics (per period with date validation)
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.exceptions import (
    InvalidRequestError,
    NotFoundError,
)
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.deployment.types import OrderDirection
from ai.backend.common.dto.manager.group.request import GroupFilter, SearchGroupsRequest
from ai.backend.common.dto.manager.group.response import (
    DeleteGroupResponse,
    PurgeGroupResponse,
    SearchGroupsResponse,
)
from ai.backend.common.dto.manager.group.types import GroupOrder, GroupOrderField
from ai.backend.common.dto.manager.infra.request import UsagePerPeriodRequest
from ai.backend.common.dto.manager.infra.response import UsagePerPeriodResponse
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, ResourceSlot
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow, KernelStatus
from ai.backend.manager.models.vfolder import VFolderRow


@pytest.fixture()
async def test_group_for_deletion(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Create a test group specifically for deletion/purge tests."""
    group_id = uuid.uuid4()
    group_name = f"delete-test-{secrets.token_hex(4)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=group_id,
                name=group_name,
                description=f"Group for deletion test {group_name}",
                is_active=True,
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
    yield group_id
    # Cleanup: force delete if still exists
    async with db_engine.begin() as conn:
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))


@pytest.fixture()
async def group_with_vfolder_mounted(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
    regular_user_fixture: Any,
) -> AsyncIterator[uuid.UUID]:
    """Create group with vfolder mounted to active kernel."""
    group_id = uuid.uuid4()
    group_name = f"group-vf-{secrets.token_hex(4)}"
    vfolder_id = uuid.uuid4()
    kernel_id = uuid.uuid4()
    user_uuid = regular_user_fixture.user_uuid

    async with db_engine.begin() as conn:
        # Create group
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=group_id,
                name=group_name,
                description="Group with mounted vfolder",
                is_active=True,
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        # Create vfolder
        await conn.execute(
            sa.insert(VFolderRow.__table__).values(
                id=vfolder_id,
                name=f"vf-{secrets.token_hex(4)}",
                user=user_uuid,
                group=group_id,
                host="local",
                domain_name=domain_fixture,
                quota_scope_id=QuotaScopeID(QuotaScopeType.USER, user_uuid),
            )
        )
        # Create active kernel with mount
        await conn.execute(
            sa.insert(KernelRow.__table__).values(
                id=kernel_id,
                session_id=uuid.uuid4(),
                group_id=group_id,
                user_uuid=user_uuid,
                domain_name=domain_fixture,
                status=KernelStatus.RUNNING,
                image="python:3.9",
                occupied_slots=ResourceSlot({}),
                mounts=[["vfolder", f"vf-{secrets.token_hex(4)}", str(vfolder_id)]],
            )
        )

    yield group_id

    # Cleanup
    async with db_engine.begin() as conn:
        await conn.execute(
            KernelRow.__table__.delete().where(KernelRow.__table__.c.id == kernel_id)
        )
        await conn.execute(
            VFolderRow.__table__.delete().where(VFolderRow.__table__.c.id == vfolder_id)
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))


@pytest.fixture()
async def group_with_active_kernel(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
    regular_user_fixture: Any,
) -> AsyncIterator[uuid.UUID]:
    """Create group with active kernel."""
    group_id = uuid.uuid4()
    group_name = f"group-ak-{secrets.token_hex(4)}"
    kernel_id = uuid.uuid4()
    user_uuid = regular_user_fixture.user_uuid

    async with db_engine.begin() as conn:
        # Create group
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=group_id,
                name=group_name,
                description="Group with active kernel",
                is_active=True,
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        # Create active kernel
        await conn.execute(
            sa.insert(KernelRow.__table__).values(
                id=kernel_id,
                session_id=uuid.uuid4(),
                group_id=group_id,
                user_uuid=user_uuid,
                domain_name=domain_fixture,
                status=KernelStatus.RUNNING,
                image="python:3.9",
                occupied_slots=ResourceSlot({}),
            )
        )

    yield group_id

    # Cleanup
    async with db_engine.begin() as conn:
        await conn.execute(
            KernelRow.__table__.delete().where(KernelRow.__table__.c.id == kernel_id)
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))


@pytest.fixture()
async def group_with_active_endpoint(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
    regular_user_fixture: Any,
    scaling_group_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Create group with active endpoint."""
    group_id = uuid.uuid4()
    group_name = f"group-ep-{secrets.token_hex(4)}"
    endpoint_id = uuid.uuid4()
    user_uuid = regular_user_fixture.user_uuid

    async with db_engine.begin() as conn:
        # Create group
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=group_id,
                name=group_name,
                description="Group with active endpoint",
                is_active=True,
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        # Create active endpoint
        await conn.execute(
            sa.insert(EndpointRow.__table__).values(
                id=endpoint_id,
                name=f"ep-{secrets.token_hex(4)}",
                project=group_id,
                domain=domain_fixture,
                created_user=user_uuid,
                session_owner=user_uuid,
                resource_group=scaling_group_fixture,
                resource_slots=ResourceSlot({}),
                lifecycle_stage=EndpointLifecycle.CREATED,
            )
        )

    yield group_id

    # Cleanup
    async with db_engine.begin() as conn:
        await conn.execute(
            EndpointRow.__table__.delete().where(EndpointRow.__table__.c.id == endpoint_id)
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))


@pytest.fixture()
async def multiple_test_groups(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[list[uuid.UUID]]:
    """Create multiple test groups for search tests."""
    group_ids = []
    unique = secrets.token_hex(4)

    async with db_engine.begin() as conn:
        for i in range(5):
            group_id = uuid.uuid4()
            await conn.execute(
                sa.insert(GroupRow.__table__).values(
                    id=group_id,
                    name=f"search-test-{unique}-{i}",
                    description=f"Search test group {i}",
                    is_active=True,
                    domain_name=domain_fixture,
                    resource_policy=resource_policy_fixture,
                )
            )
            group_ids.append(group_id)

    yield group_ids

    # Cleanup
    async with db_engine.begin() as conn:
        for group_id in group_ids:
            await conn.execute(
                GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id)
            )


class TestGroupDelete:
    """Tests for soft delete (DELETE /groups/{id})."""

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups/{id} DELETE route not yet implemented",
        raises=NotFoundError,
    )
    async def test_admin_soft_deletes_group(
        self,
        admin_registry: BackendAIClientRegistry,
        test_group_for_deletion: uuid.UUID,
    ) -> None:
        """S-1: Admin soft deletes group → group status transitions to inactive."""
        result = await admin_registry.group.delete(test_group_for_deletion)
        assert isinstance(result, DeleteGroupResponse)
        assert result.deleted is True

    async def test_delete_nonexistent_group_raises_404(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-1: Delete non-existent group → 404."""
        nonexistent_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await admin_registry.group.delete(nonexistent_id)

    async def test_regular_user_cannot_delete_group(
        self,
        user_registry: BackendAIClientRegistry,
        test_group_for_deletion: uuid.UUID,
    ) -> None:
        """F-AUTH-1: Regular user cannot delete group → 404 (route not accessible)."""
        with pytest.raises(NotFoundError):
            await user_registry.group.delete(test_group_for_deletion)


class TestGroupPurge:
    """Tests for hard purge with validation."""

    @pytest.mark.xfail(
        strict=True,
        reason="Purge action not exposed via REST API yet",
        raises=NotFoundError,
    )
    async def test_admin_hard_purges_group(
        self,
        admin_registry: BackendAIClientRegistry,
        test_group_for_deletion: uuid.UUID,
        db_engine: SAEngine,
    ) -> None:
        """S-1: Admin hard purges group → group removed from DB."""
        # Verify group exists before purge
        group = await admin_registry.group.get(test_group_for_deletion)
        assert group.group.id == test_group_for_deletion

        # Purge the group
        result = await admin_registry.group.purge(test_group_for_deletion)
        assert isinstance(result, PurgeGroupResponse)
        assert result.purged is True

        # Verify group is completely removed from DB
        async with db_engine.begin() as conn:
            query_result = await conn.execute(
                sa.select(GroupRow.__table__).where(
                    GroupRow.__table__.c.id == test_group_for_deletion
                )
            )
            row = query_result.fetchone()
            assert row is None, "Group should be completely removed from DB after purge"

    @pytest.mark.xfail(
        strict=True,
        reason="Purge action not exposed via REST API yet",
        raises=NotFoundError,
    )
    async def test_purge_group_with_vfolder_mounts_blocked(
        self,
        admin_registry: BackendAIClientRegistry,
        group_with_vfolder_mounted: uuid.UUID,
    ) -> None:
        """F-BIZ-1: Purge group with vfolder mounts → blocked with error."""
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.group.purge(group_with_vfolder_mounted)
        # Verify error indicates vfolder mount blocking
        assert exc_info.value.status in (400, 409)  # Bad Request or Conflict

    @pytest.mark.xfail(
        strict=True,
        reason="Purge action not exposed via REST API yet",
        raises=NotFoundError,
    )
    async def test_purge_group_with_active_kernels_blocked(
        self,
        admin_registry: BackendAIClientRegistry,
        group_with_active_kernel: uuid.UUID,
    ) -> None:
        """F-BIZ-2: Purge group with active kernels → blocked with error."""
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.group.purge(group_with_active_kernel)
        # Verify error indicates active kernel blocking
        assert exc_info.value.status in (400, 409)  # Bad Request or Conflict

    @pytest.mark.xfail(
        strict=True,
        reason="Purge action not exposed via REST API yet",
        raises=NotFoundError,
    )
    async def test_purge_group_with_active_endpoints_blocked(
        self,
        admin_registry: BackendAIClientRegistry,
        group_with_active_endpoint: uuid.UUID,
    ) -> None:
        """F-BIZ-3: Purge group with active endpoints → blocked with error."""
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.group.purge(group_with_active_endpoint)
        # Verify error indicates active endpoint blocking
        assert exc_info.value.status in (400, 409)  # Bad Request or Conflict


class TestGroupSearch:
    """Tests for project search with filters and pagination."""

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups search route not yet implemented",
        raises=NotFoundError,
    )
    async def test_search_all_projects_returns_paginated_list(
        self,
        admin_registry: BackendAIClientRegistry,
        multiple_test_groups: list[uuid.UUID],
    ) -> None:
        """S-1: Search all projects → returns paginated list."""
        result = await admin_registry.group.search(
            SearchGroupsRequest(limit=10, offset=0),
        )
        assert isinstance(result, SearchGroupsResponse)
        assert len(result.groups) > 0
        assert result.pagination.total >= len(multiple_test_groups)

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups search route not yet implemented",
        raises=NotFoundError,
    )
    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        multiple_test_groups: list[uuid.UUID],
        db_engine: SAEngine,
    ) -> None:
        """S-2: Search with name filter → matching groups."""
        # Get actual name of one of the test groups
        async with db_engine.begin() as conn:
            query_result = await conn.execute(
                sa.select(GroupRow.__table__.c.name).where(
                    GroupRow.__table__.c.id == multiple_test_groups[0]
                )
            )
            group_name = query_result.scalar_one()

        result = await admin_registry.group.search(
            SearchGroupsRequest(
                filter=GroupFilter(name=StringFilter(contains=group_name[:10])),
                limit=10,
            ),
        )
        assert isinstance(result, SearchGroupsResponse)
        # All returned groups should have names containing the filter
        for group in result.groups:
            assert group_name[:10] in group.name

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups search route not yet implemented",
        raises=NotFoundError,
    )
    async def test_search_with_domain_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        """S-3: Search with domain filter → groups in domain."""
        result = await admin_registry.group.search(
            SearchGroupsRequest(
                filter=GroupFilter(domain_name=StringFilter(equals=domain_fixture)),
                limit=10,
            ),
        )
        assert isinstance(result, SearchGroupsResponse)
        for group in result.groups:
            assert group.domain_name == domain_fixture

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups search route not yet implemented",
        raises=NotFoundError,
    )
    async def test_search_with_sorting(
        self,
        admin_registry: BackendAIClientRegistry,
        multiple_test_groups: list[uuid.UUID],
    ) -> None:
        """S-4: Search with sorting → correctly ordered."""
        # Search with ascending name order
        asc_result = await admin_registry.group.search(
            SearchGroupsRequest(
                order=GroupOrder(field=GroupOrderField.NAME, direction=OrderDirection.ASC),
                limit=10,
            ),
        )
        assert isinstance(asc_result, SearchGroupsResponse)
        # Verify results are sorted by name ascending
        names_asc = [g.name for g in asc_result.groups]
        assert names_asc == sorted(names_asc)

        # Search with descending name order
        desc_result = await admin_registry.group.search(
            SearchGroupsRequest(
                order=GroupOrder(field=GroupOrderField.NAME, direction=OrderDirection.DESC),
                limit=10,
            ),
        )
        assert isinstance(desc_result, SearchGroupsResponse)
        # Verify results are sorted by name descending
        names_desc = [g.name for g in desc_result.groups]
        assert names_desc == sorted(names_desc, reverse=True)

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups search route not yet implemented",
        raises=NotFoundError,
    )
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
        multiple_test_groups: list[uuid.UUID],
    ) -> None:
        """S-5: Search with pagination → correct page."""
        # Page 1
        page1 = await admin_registry.group.search(
            SearchGroupsRequest(limit=2, offset=0),
        )
        # Page 2
        page2 = await admin_registry.group.search(
            SearchGroupsRequest(limit=2, offset=2),
        )
        assert isinstance(page1, SearchGroupsResponse)
        assert isinstance(page2, SearchGroupsResponse)
        # Ensure pages are different
        page1_ids = {g.id for g in page1.groups}
        page2_ids = {g.id for g in page2.groups}
        assert page1_ids != page2_ids

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups search route not yet implemented",
        raises=NotFoundError,
    )
    async def test_search_empty_result(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-6: Empty result → total=0, empty items."""
        result = await admin_registry.group.search(
            SearchGroupsRequest(
                filter=GroupFilter(
                    name=StringFilter(equals=f"nonexistent-group-{secrets.token_hex(16)}")
                ),
            ),
        )
        assert isinstance(result, SearchGroupsResponse)
        assert result.pagination.total == 0
        assert len(result.groups) == 0


class TestGroupUsageStats:
    """Tests for usage statistics per period."""

    @pytest.mark.xfail(
        strict=True,
        reason="Usage per period action not exposed via REST API yet",
        raises=NotFoundError,
    )
    async def test_get_usage_per_period(
        self,
        admin_registry: BackendAIClientRegistry,
        test_group_for_deletion: uuid.UUID,
    ) -> None:
        """S-1: Get usage per period → returns usage data."""
        # Valid 30-day period
        result = await admin_registry.infra.get_usage_per_period(
            UsagePerPeriodRequest(
                project_id=str(test_group_for_deletion),
                start_date="20260101",
                end_date="20260131",
            )
        )
        assert isinstance(result, UsagePerPeriodResponse)
        assert isinstance(result.root, list)
        # Empty result is expected since test group has no sessions

    @pytest.mark.xfail(
        strict=True,
        reason="Usage per period action not exposed via REST API yet",
        raises=NotFoundError,
    )
    async def test_usage_100_day_max_range_enforced(
        self,
        admin_registry: BackendAIClientRegistry,
        test_group_for_deletion: uuid.UUID,
    ) -> None:
        """F-BIZ-1: 100-day max range enforced → error if range exceeds 100 days."""
        # 101 days: 20260101 to 20260412 (Jan 1 to Apr 12 = 101 days)
        with pytest.raises(InvalidRequestError) as exc_info:
            await admin_registry.infra.get_usage_per_period(
                UsagePerPeriodRequest(
                    project_id=str(test_group_for_deletion),
                    start_date="20260101",
                    end_date="20260412",  # More than 100 days after start_date
                )
            )
        assert "100 days" in str(exc_info.value).lower()

    @pytest.mark.xfail(
        strict=True,
        reason="Usage per period action not exposed via REST API yet",
        raises=NotFoundError,
    )
    async def test_usage_end_date_validation(
        self,
        admin_registry: BackendAIClientRegistry,
        test_group_for_deletion: uuid.UUID,
    ) -> None:
        """F-BIZ-2: end_date > start_date validation → error if end_date <= start_date."""
        # end_date same as start_date
        with pytest.raises(InvalidRequestError) as exc_info:
            await admin_registry.infra.get_usage_per_period(
                UsagePerPeriodRequest(
                    project_id=str(test_group_for_deletion),
                    start_date="20260115",
                    end_date="20260115",  # Same date
                )
            )
        assert "end_date must be later than start_date" in str(exc_info.value).lower()

        # end_date before start_date
        with pytest.raises(InvalidRequestError) as exc_info:
            await admin_registry.infra.get_usage_per_period(
                UsagePerPeriodRequest(
                    project_id=str(test_group_for_deletion),
                    start_date="20260115",
                    end_date="20260110",  # Before start_date
                )
            )
        assert "end_date must be later than start_date" in str(exc_info.value).lower()

    @pytest.mark.xfail(
        strict=True,
        reason="Usage per period action not exposed via REST API yet",
        raises=NotFoundError,
    )
    async def test_usage_for_group_with_no_sessions(
        self,
        admin_registry: BackendAIClientRegistry,
        test_group_for_deletion: uuid.UUID,
    ) -> None:
        """S-2: Usage for group with no sessions → empty/zero usage."""
        result = await admin_registry.infra.get_usage_per_period(
            UsagePerPeriodRequest(
                project_id=str(test_group_for_deletion),
                start_date="20260101",
                end_date="20260131",
            )
        )
        assert isinstance(result, UsagePerPeriodResponse)
        assert isinstance(result.root, list)
        assert len(result.root) == 0, "Group with no sessions should return empty usage list"
