"""
Tests for ScalingGroupRepository functionality.
Tests the repository layer with real database operations.
"""

from collections.abc import AsyncGenerator, Callable, Mapping
from datetime import datetime
from typing import Any, Optional

import pytest
import sqlalchemy as sa

from ai.backend.common.types import SessionTypes
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
from ai.backend.manager.repositories.scaling_group.updaters import ScalingGroupUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


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

    async def test_search_scaling_groups_all(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test searching all scaling groups without filters"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        # Should have exactly 5 test scaling groups
        assert len(result.items) == 5
        assert result.total_count == 5

        # Verify test scaling groups are in results
        result_names = {sg.name for sg in result.items}
        for test_sg_name in sample_scaling_groups_small:
            assert test_sg_name in result_names

    async def test_search_scaling_groups_with_querier(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_small: list[str],
    ) -> None:
        """Test searching scaling groups with querier"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) == 5
        assert result.total_count == 5

    # Pagination Tests

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
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) == expected_items
        assert result.total_count == total_count

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
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        assert len(result.items) == expected_items
        assert result.total_count == total_count

    async def test_search_scaling_groups_large_limit(
        self,
        scaling_group_repository: ScalingGroupRepository,
        sample_scaling_groups_medium: list[str],
    ) -> None:
        """Test searching scaling groups with large limit returns all items"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scaling_group_repository.search_scaling_groups(querier=querier)

        # Should have exactly 15 test scaling groups
        assert len(result.items) == 15
        assert result.total_count == 15

    # Update Tests

    @pytest.fixture
    async def scaling_group_for_update(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create a single scaling group for update testing"""
        async with db_with_cleanup.begin_session() as db_sess:
            sgroup = ScalingGroupRow(
                name="test-sgroup-update",
                description="Original description",
                is_active=True,
                is_public=True,
                created_at=datetime.now(),
                wsproxy_addr="http://original:5000",
                wsproxy_api_token=None,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
                use_host_network=False,
            )
            db_sess.add(sgroup)
            await db_sess.flush()
        return "test-sgroup-update"

    def _create_scaling_group_updater(
        self,
        name: str,
        description: Optional[TriState[str]] = None,
        is_active: Optional[OptionalState[bool]] = None,
        is_public: Optional[OptionalState[bool]] = None,
        wsproxy_addr: Optional[TriState[str]] = None,
        wsproxy_api_token: Optional[TriState[str]] = None,
        driver: Optional[OptionalState[str]] = None,
        driver_opts: Optional[OptionalState[Mapping[str, Any]]] = None,
        scheduler: Optional[OptionalState[str]] = None,
        scheduler_opts: Optional[OptionalState[ScalingGroupOpts]] = None,
        use_host_network: Optional[OptionalState[bool]] = None,
    ) -> Updater[ScalingGroupRow]:
        """Create a ScalingGroupUpdaterSpec with the given parameters."""
        spec = ScalingGroupUpdaterSpec(
            description=description if description is not None else TriState.nop(),
            is_active=is_active if is_active is not None else OptionalState.nop(),
            is_public=is_public if is_public is not None else OptionalState.nop(),
            wsproxy_addr=wsproxy_addr if wsproxy_addr is not None else TriState.nop(),
            wsproxy_api_token=(
                wsproxy_api_token if wsproxy_api_token is not None else TriState.nop()
            ),
            driver=driver if driver is not None else OptionalState.nop(),
            driver_opts=driver_opts if driver_opts is not None else OptionalState.nop(),
            scheduler=scheduler if scheduler is not None else OptionalState.nop(),
            scheduler_opts=scheduler_opts if scheduler_opts is not None else OptionalState.nop(),
            use_host_network=(
                use_host_network if use_host_network is not None else OptionalState.nop()
            ),
        )
        return Updater(spec=spec, pk_value=name)

    async def test_update_scaling_group_success(
        self,
        scaling_group_repository: ScalingGroupRepository,
        scaling_group_for_update: str,
    ) -> None:
        """Test updating a scaling group"""
        new_scheduler_opts = ScalingGroupOpts(
            allowed_session_types=[SessionTypes.BATCH],
            config={"updated": True},
        )
        updater = self._create_scaling_group_updater(
            name=scaling_group_for_update,
            description=TriState.update("Updated description"),
            is_active=OptionalState.update(False),
            is_public=OptionalState.update(False),
            wsproxy_addr=TriState.update("http://new-wsproxy:5000"),
            wsproxy_api_token=TriState.update("new-token"),
            driver=OptionalState.update("docker"),
            driver_opts=OptionalState.update({"new_opt": "value"}),
            scheduler=OptionalState.update("drf"),
            scheduler_opts=OptionalState.update(new_scheduler_opts),
            use_host_network=OptionalState.update(True),
        )
        result = await scaling_group_repository.update_scaling_group(updater)

        assert result.metadata.description == "Updated description"
        assert result.status.is_active is False
        assert result.status.is_public is False
        assert result.network.wsproxy_addr == "http://new-wsproxy:5000"
        assert result.network.wsproxy_api_token == "new-token"
        assert result.driver.name == "docker"
        assert result.driver.options == {"new_opt": "value"}
        assert result.scheduler.name.value == "drf"
        assert result.network.use_host_network is True

    async def test_update_scaling_group_not_found(
        self,
        scaling_group_repository: ScalingGroupRepository,
    ) -> None:
        """Test updating a non-existent scaling group raises ScalingGroupNotFound"""
        updater = self._create_scaling_group_updater(
            name="test-sgroup-nonexistent",
            description=TriState.update("Updated description"),
        )

        with pytest.raises(ScalingGroupNotFound):
            await scaling_group_repository.update_scaling_group(updater)
