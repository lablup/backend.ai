"""
Tests for ScalingGroupRepository functionality.
Tests the repository layer with real database operations.
"""

from collections.abc import AsyncGenerator, Callable
from datetime import datetime

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

    async def _create_scaling_groups(
        self,
        db_engine: ExtendedAsyncSAEngine,
        count: int,
        prefix: str,
        is_active_func: Callable[[int], bool] = lambda i: True,
    ) -> list[str]:
        """Helper to create scaling groups with given parameters"""
        scaling_group_names = []
        async with db_engine.begin_session() as db_sess:
            for i in range(count):
                sgroup_name = f"test-sgroup-{prefix}-{i:02d}"
                sgroup = ScalingGroupRow(
                    name=sgroup_name,
                    description=f"Test scaling group {i:02d}",
                    is_active=is_active_func(i),
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
        return scaling_group_names

    @pytest.fixture
    async def sample_scaling_groups_small(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 5 sample scaling groups for basic testing"""
        yield await self._create_scaling_groups(db_with_cleanup, 5, "small")

    @pytest.fixture
    async def sample_scaling_groups_for_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 25 sample scaling groups for pagination testing"""
        yield await self._create_scaling_groups(db_with_cleanup, 25, "pagination")

    @pytest.fixture
    async def sample_scaling_groups_mixed_active(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 20 sample scaling groups (10 active, 10 inactive) for filter testing"""
        yield await self._create_scaling_groups(
            db_with_cleanup, 20, "mixed", is_active_func=lambda i: i % 2 == 0
        )

    @pytest.fixture
    async def sample_scaling_groups_medium(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[list[str], None]:
        """Create 15 sample scaling groups for no-pagination testing"""
        yield await self._create_scaling_groups(db_with_cleanup, 15, "medium")

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

        # Should have exactly 5 test scaling groups
        assert len(result.items) == 5
        assert result.total_count == 5

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

        assert len(result.items) == 5
        assert result.total_count == 5

    # Pagination Tests

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "limit,offset,expected_items,total_count,description",
        [
            (10, 0, 10, 25, "first page"),
            (10, 10, 10, 25, "second page"),
            (10, 20, 5, 25, "last page with partial results"),
        ],
        ids=["first_page", "second_page", "last_page"],
    )
    async def test_search_scaling_groups_offset_pagination(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_for_pagination: list[str],
        limit: int,
        offset: int,
        expected_items: int,
        total_count: int,
        description: str,
    ) -> None:
        """Test offset-based pagination scenarios"""
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) == expected_items
        assert result.total_count == total_count

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "limit,offset,expected_items,total_count,description",
        [
            (100, 0, 5, 5, "limit exceeds total count"),
            (10, 10000, 0, 5, "offset exceeds total count"),
        ],
        ids=["limit_exceeds", "offset_exceeds"],
    )
    async def test_search_scaling_groups_pagination_edge_cases(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
        limit: int,
        offset: int,
        expected_items: int,
        total_count: int,
        description: str,
    ) -> None:
        """Test pagination edge cases"""
        querier = Querier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) == expected_items
        assert result.total_count == total_count

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

        # Should have exactly 15 test scaling groups
        assert len(result.items) == 15
        assert result.total_count == 15
