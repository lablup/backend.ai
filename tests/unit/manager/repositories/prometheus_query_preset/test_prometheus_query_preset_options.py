"""Tests for PrometheusQueryPreset query options (conditions and orders)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset.row import PresetOptions
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
)
from ai.backend.manager.repositories.prometheus_query_preset import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.repositories.prometheus_query_preset.options import (
    PrometheusQueryPresetConditions,
    PrometheusQueryPresetOrders,
)
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class PresetSeed:
    """A single preset row to seed into the database."""

    name: str
    metric_name: str = "backendai_metric"
    query_template: str = "{metric_name}{{{labels}}}"
    time_window: str | None = "5m"
    filter_labels: tuple[str, ...] = ()
    group_labels: tuple[str, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class SearchCase:
    """Base test case carrying seeds for DB fixture."""

    seeds: tuple[PresetSeed, ...]


@dataclass
class ConditionCase(SearchCase):
    """Test case for condition-based search."""

    conditions: list[Any] = field(default_factory=list)
    expected_count: int = 0
    expected_names: frozenset[str] = frozenset()


@dataclass
class OrderCase(SearchCase):
    """Test case for order-based search."""

    orders: list[Any] = field(default_factory=list)
    expected_ordered_names: tuple[str, ...] = ()


@dataclass
class SearchContext:
    """Returned by the search_ctx fixture."""

    preset_ids: list[uuid.UUID]
    case: SearchCase


_base_time = datetime(2026, 1, 1, tzinfo=UTC)


class TestPrometheusQueryPresetOptions:
    """Test cases for prometheus query preset query conditions and orders."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [PrometheusQueryPresetRow],
        ):
            yield database_connection

    @pytest.fixture
    def preset_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> PrometheusQueryPresetRepository:
        return PrometheusQueryPresetRepository(db=db_with_cleanup)

    async def _seed_presets(
        self,
        seeds: tuple[PresetSeed, ...],
        db: ExtendedAsyncSAEngine,
    ) -> list[uuid.UUID]:
        now = datetime.now(tz=UTC)
        preset_ids = [uuid.uuid4() for _ in seeds]
        rows = [
            PrometheusQueryPresetRow(
                id=preset_ids[i],
                name=seed.name,
                metric_name=seed.metric_name,
                query_template=seed.query_template,
                time_window=seed.time_window,
                options=PresetOptions(
                    filter_labels=list(seed.filter_labels),
                    group_labels=list(seed.group_labels),
                ),
                created_at=seed.created_at or now,
                updated_at=seed.updated_at or now,
            )
            for i, seed in enumerate(seeds)
        ]
        async with db.begin_session() as db_sess:
            db_sess.add_all(rows)
            await db_sess.flush()
        return preset_ids

    @pytest.fixture
    async def test_case(
        self,
        request: pytest.FixtureRequest,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> SearchContext:
        case: SearchCase = request.param
        preset_ids = await self._seed_presets(case.seeds, db_with_cleanup)
        return SearchContext(preset_ids=preset_ids, case=case)

    @pytest.mark.parametrize(
        "test_case",
        [
            ConditionCase(
                seeds=(
                    PresetSeed(name="Container CPU Rate", metric_name="backendai_cpu"),
                    PresetSeed(name="container cpu rate", metric_name="backendai_cpu"),
                    PresetSeed(name="GPU Memory Usage", metric_name="backendai_gpu"),
                ),
                conditions=[
                    PrometheusQueryPresetConditions.by_name_contains(
                        StringMatchSpec("Container", case_insensitive=False, negated=False)
                    )
                ],
                expected_count=1,
                expected_names=frozenset({"Container CPU Rate"}),
            ),
            ConditionCase(
                seeds=(
                    PresetSeed(name="Container CPU Rate", metric_name="backendai_cpu"),
                    PresetSeed(name="container cpu rate", metric_name="backendai_cpu"),
                    PresetSeed(name="GPU Memory Usage", metric_name="backendai_gpu"),
                ),
                conditions=[
                    PrometheusQueryPresetConditions.by_name_contains(
                        StringMatchSpec("container", case_insensitive=True, negated=False)
                    )
                ],
                expected_count=2,
                expected_names=frozenset({"Container CPU Rate", "container cpu rate"}),
            ),
            ConditionCase(
                seeds=(
                    PresetSeed(name="Container CPU Rate"),
                    PresetSeed(name="container cpu rate"),
                ),
                conditions=[
                    PrometheusQueryPresetConditions.by_name_equals(
                        StringMatchSpec("Container CPU Rate", case_insensitive=False, negated=False)
                    )
                ],
                expected_count=1,
                expected_names=frozenset({"Container CPU Rate"}),
            ),
            ConditionCase(
                seeds=(PresetSeed(name="Existing Preset"),),
                conditions=[
                    PrometheusQueryPresetConditions.by_name_equals(
                        StringMatchSpec("NonexistentPreset", case_insensitive=False, negated=False)
                    )
                ],
                expected_count=0,
                expected_names=frozenset(),
            ),
        ],
        indirect=True,
    )
    async def test_search_by_condition(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        test_case: SearchContext,
    ) -> None:
        assert isinstance(
            test_case.case, ConditionCase
        )  # ensure type checker understands the case type for accessing expected fields
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=test_case.case.conditions,
            orders=[],
        )
        result = await preset_repository.search(querier=querier)

        assert len(result.items) == test_case.case.expected_count
        assert result.total_count == test_case.case.expected_count
        assert {p.name for p in result.items} == test_case.case.expected_names

    @pytest.fixture
    async def ids_presets(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> list[uuid.UUID]:
        return await self._seed_presets(
            (PresetSeed(name="A"), PresetSeed(name="B"), PresetSeed(name="C")),
            db_with_cleanup,
        )

    async def test_search_by_ids(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        ids_presets: list[uuid.UUID],
    ) -> None:
        target_ids = ids_presets[:2]
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[PrometheusQueryPresetConditions.by_ids(target_ids)],
            orders=[],
        )
        result = await preset_repository.search(querier=querier)

        assert len(result.items) == 2
        assert {p.id for p in result.items} == set(target_ids)

    @pytest.mark.parametrize(
        "test_case",
        [
            OrderCase(
                seeds=(
                    PresetSeed(name="Zebra Preset", created_at=_base_time - timedelta(days=3)),
                    PresetSeed(name="Alpha Preset", created_at=_base_time - timedelta(days=2)),
                    PresetSeed(name="Beta Preset", created_at=_base_time - timedelta(days=1)),
                ),
                orders=[PrometheusQueryPresetOrders.name(ascending=True)],
                expected_ordered_names=("Alpha Preset", "Beta Preset", "Zebra Preset"),
            ),
            OrderCase(
                seeds=(
                    PresetSeed(name="Zebra Preset", created_at=_base_time - timedelta(days=3)),
                    PresetSeed(name="Alpha Preset", created_at=_base_time - timedelta(days=2)),
                    PresetSeed(name="Beta Preset", created_at=_base_time - timedelta(days=1)),
                ),
                orders=[PrometheusQueryPresetOrders.name(ascending=False)],
                expected_ordered_names=("Zebra Preset", "Beta Preset", "Alpha Preset"),
            ),
            OrderCase(
                seeds=(
                    PresetSeed(name="Zebra Preset", created_at=_base_time - timedelta(days=3)),
                    PresetSeed(name="Alpha Preset", created_at=_base_time - timedelta(days=2)),
                    PresetSeed(name="Beta Preset", created_at=_base_time - timedelta(days=1)),
                ),
                orders=[PrometheusQueryPresetOrders.created_at(ascending=True)],
                expected_ordered_names=("Zebra Preset", "Alpha Preset", "Beta Preset"),
            ),
            OrderCase(
                seeds=(
                    PresetSeed(name="Zebra Preset", created_at=_base_time - timedelta(days=3)),
                    PresetSeed(name="Alpha Preset", created_at=_base_time - timedelta(days=2)),
                    PresetSeed(name="Beta Preset", created_at=_base_time - timedelta(days=1)),
                ),
                orders=[PrometheusQueryPresetOrders.created_at(ascending=False)],
                expected_ordered_names=("Beta Preset", "Alpha Preset", "Zebra Preset"),
            ),
        ],
        indirect=True,
    )
    async def test_search_with_order(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        test_case: SearchContext,
    ) -> None:
        assert isinstance(test_case.case, OrderCase), (
            f"Expected OrderCase but got {type(test_case.case).__name__}"
        )
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1000, offset=0),
            conditions=[],
            orders=test_case.case.orders,
        )
        result = await preset_repository.search(querier=querier)

        assert tuple(p.name for p in result.items) == test_case.case.expected_ordered_names
