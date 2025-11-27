"""
Tests for ScalingGroupRepository functionality.
Tests the repository layer with real database operations.
"""

from datetime import datetime
from typing import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import OffsetPagination, Querier
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository


class TestScalingGroupRepositoryDB:
    """Test cases for ScalingGroupRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans scaling group data after each test"""
        yield database_engine

        # Cleanup all scaling groups created during test
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(
                sa.delete(ScalingGroupRow).where(ScalingGroupRow.name.like("test-sgroup-%")),
                execution_options={"synchronize_session": False},
            )

    @pytest.fixture
    async def sample_scaling_groups_small(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 5 sample scaling groups for basic testing"""
        scaling_group_names = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                sgroup_name = f"test-sgroup-small-{i}"
                sgroup = ScalingGroupRow(
                    name=sgroup_name,
                    description=f"Test scaling group {i}",
                    is_active=True,
                    is_public=True,
                    created_at=datetime.now(),
                    wsproxy_addr=None,
                    wsproxy_api_token=None,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    use_host_network=False,
                )
                db_sess.add(sgroup)
                scaling_group_names.append(sgroup_name)
            await db_sess.flush()

        yield scaling_group_names

    @pytest.fixture
    async def sample_scaling_groups_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 25 sample scaling groups for pagination testing"""
        scaling_group_names = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(25):
                sgroup_name = f"test-sgroup-pagination-{i:02d}"
                sgroup = ScalingGroupRow(
                    name=sgroup_name,
                    description=f"Test scaling group {i:02d}",
                    is_active=True,
                    is_public=True,
                    created_at=datetime.now(),
                    wsproxy_addr=None,
                    wsproxy_api_token=None,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    use_host_network=False,
                )
                db_sess.add(sgroup)
                scaling_group_names.append(sgroup_name)
            await db_sess.flush()

        yield scaling_group_names

    @pytest.fixture
    async def sample_scaling_groups_mixed_active(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 20 sample scaling groups (10 active, 10 inactive) for filter testing"""
        scaling_group_names = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(20):
                sgroup_name = f"test-sgroup-mixed-{i:02d}"
                sgroup = ScalingGroupRow(
                    name=sgroup_name,
                    description=f"Test scaling group {i:02d}",
                    is_active=(i % 2 == 0),  # Even indexes active
                    is_public=True,
                    created_at=datetime.now(),
                    wsproxy_addr=None,
                    wsproxy_api_token=None,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    use_host_network=False,
                )
                db_sess.add(sgroup)
                scaling_group_names.append(sgroup_name)
            await db_sess.flush()

        yield scaling_group_names

    @pytest.fixture
    async def sample_scaling_groups_medium(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 15 sample scaling groups for no-pagination testing"""
        scaling_group_names = []
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(15):
                sgroup_name = f"test-sgroup-medium-{i}"
                sgroup = ScalingGroupRow(
                    name=sgroup_name,
                    description=f"Test scaling group {i}",
                    is_active=True,
                    is_public=True,
                    created_at=datetime.now(),
                    wsproxy_addr=None,
                    wsproxy_api_token=None,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    use_host_network=False,
                )
                db_sess.add(sgroup)
                scaling_group_names.append(sgroup_name)
            await db_sess.flush()

        yield scaling_group_names

    @pytest.fixture
    async def scaling_group_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ScalingGroupRepository, None]:
        """Create ScalingGroupRepository instance with database"""
        repo = ScalingGroupRepository(db=db_with_cleanup)
        yield repo

    @pytest.mark.asyncio
    async def test_search_scaling_groups_all(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test searching all scaling groups without filters"""
        result = await scaling_group_repository.search_scaling_groups()

        # Should have at least the 5 test scaling groups
        assert len(result.items) >= 5
        assert result.total_count >= 5

        # Verify test scaling groups are in results
        result_names = {sg.name for sg in result.items}
        for test_sg_name in sample_scaling_groups_small:
            assert test_sg_name in result_names

    @pytest.mark.asyncio
    async def test_search_scaling_groups_with_querier(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test searching scaling groups with querier"""
        querier = Querier(
            conditions=[],
            orders=[],
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) >= 5
        assert result.total_count >= 5

    # Pagination Tests

    @pytest.mark.asyncio
    async def test_search_scaling_groups_offset_pagination_first_page(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_for_pagination: list[str],
    ) -> None:
        """Test first page of offset-based pagination"""
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) == 10
        assert result.total_count >= 25

    @pytest.mark.asyncio
    async def test_search_scaling_groups_offset_pagination_second_page(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_for_pagination: list[str],
    ) -> None:
        """Test second page of offset-based pagination"""
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=10),
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) == 10
        assert result.total_count >= 25

    @pytest.mark.asyncio
    async def test_search_scaling_groups_offset_pagination_last_page(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_for_pagination: list[str],
    ) -> None:
        """Test last page of offset-based pagination with partial results"""
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=20),
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        # Should have at least 5 items (our test data)
        assert len(result.items) >= 5
        assert result.total_count >= 25

    @pytest.mark.asyncio
    async def test_search_scaling_groups_pagination_limit_exceeds_total(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test pagination when limit exceeds total count"""
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=100, offset=0),
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        # Should return all items
        assert len(result.items) >= 5
        assert result.total_count >= 5

    @pytest.mark.asyncio
    async def test_search_scaling_groups_pagination_offset_exceeds_total(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test pagination when offset exceeds total count returns empty"""
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=10000),
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) == 0
        # Total count should still reflect actual number of items
        assert result.total_count >= 5

    @pytest.mark.asyncio
    async def test_search_scaling_groups_no_pagination(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_medium: list[str],
    ) -> None:
        """Test searching scaling groups without pagination returns all items"""
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=None,
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        # Should have at least 15 test scaling groups
        assert len(result.items) >= 15
        assert result.total_count >= 15

    @pytest.mark.asyncio
    async def test_search_scaling_groups_data_structure(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test that returned data structure is correct"""
        result = await scaling_group_repository.search_scaling_groups()

        assert hasattr(result, "items")
        assert hasattr(result, "total_count")
        assert isinstance(result.items, list)
        assert isinstance(result.total_count, int)

        # Check first item structure
        if result.items:
            first_item = result.items[0]
            assert hasattr(first_item, "name")
            assert hasattr(first_item, "description")
            assert hasattr(first_item, "is_active")
            assert hasattr(first_item, "is_public")
            assert hasattr(first_item, "created_at")
            assert hasattr(first_item, "driver")
            assert hasattr(first_item, "scheduler")
            assert hasattr(first_item, "use_host_network")
