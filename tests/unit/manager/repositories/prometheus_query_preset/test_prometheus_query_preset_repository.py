"""Tests for PrometheusQueryPresetRepository CRUD operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest

from ai.backend.common.exception import PrometheusQueryPresetNotFound
from ai.backend.manager.data.prometheus_query_preset import (
    PrometheusQueryPresetData,
)
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset.row import PresetOptions
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    OffsetPagination,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.prometheus_query_preset import (
    PrometheusQueryPresetCreatorSpec,
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.repositories.prometheus_query_preset.updaters import (
    PrometheusQueryPresetUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.db import with_tables


class TestPrometheusQueryPresetRepository:
    """Test cases for PrometheusQueryPresetRepository CRUD operations."""

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

    @pytest.fixture
    async def sample_preset_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> uuid.UUID:
        """Create a sample preset directly in DB and return its ID."""
        preset_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        async with db_with_cleanup.begin_session() as db_sess:
            row = PrometheusQueryPresetRow(
                id=preset_id,
                name="container_cpu_rate",
                metric_name="backendai_container_utilization",
                query_template="sum by ({group_by})(rate({metric_name}{{{labels}}}[{window}]))",
                time_window="5m",
                options=PresetOptions(
                    filter_labels=["container_metric_name", "kernel_id"],
                    group_labels=["kernel_id"],
                ),
                created_at=now,
                updated_at=now,
            )
            db_sess.add(row)
            await db_sess.flush()
        return preset_id

    @pytest.fixture
    async def sample_preset_ids(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> list[uuid.UUID]:
        """Create 5 sample presets directly in DB and return their IDs."""
        preset_ids: list[uuid.UUID] = []
        now = datetime.now(tz=UTC)
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                preset_id = uuid.uuid4()
                preset_ids.append(preset_id)
                row = PrometheusQueryPresetRow(
                    id=preset_id,
                    name=f"preset_{i}",
                    metric_name="backendai_metric",
                    query_template="template",
                    time_window=None,
                    options=PresetOptions(filter_labels=[], group_labels=[]),
                    created_at=now,
                    updated_at=now,
                )
                db_sess.add(row)
            await db_sess.flush()
        return preset_ids

    @pytest.mark.asyncio
    async def test_create(
        self,
        preset_repository: PrometheusQueryPresetRepository,
    ) -> None:
        name = "gpu_memory_usage"
        metric_name = "backendai_gpu_memory"
        query_template = "avg({metric_name}{{{labels}}})"
        time_window = "10m"
        filter_labels = ["kernel_id", "device_id"]
        group_labels = ["kernel_id"]

        creator = Creator(
            spec=PrometheusQueryPresetCreatorSpec(
                name=name,
                metric_name=metric_name,
                query_template=query_template,
                time_window=time_window,
                filter_labels=filter_labels,
                group_labels=group_labels,
            ),
        )

        result = await preset_repository.create(creator)

        assert isinstance(result, PrometheusQueryPresetData)
        assert result.name == name
        assert result.metric_name == metric_name
        assert result.query_template == query_template
        assert result.time_window == time_window
        assert result.filter_labels == filter_labels
        assert result.group_labels == group_labels
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_by_id(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        result = await preset_repository.get_by_id(sample_preset_id)

        assert result.id == sample_preset_id
        assert result.name == "container_cpu_rate"
        assert result.metric_name == "backendai_container_utilization"
        assert result.time_window == "5m"
        assert result.filter_labels == ["container_metric_name", "kernel_id"]
        assert result.group_labels == ["kernel_id"]

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        preset_repository: PrometheusQueryPresetRepository,
    ) -> None:
        with pytest.raises(PrometheusQueryPresetNotFound):
            await preset_repository.get_by_id(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_search(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_ids: list[uuid.UUID],
    ) -> None:
        limit = 3
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=limit, offset=0),
            conditions=[],
            orders=[],
        )
        result = await preset_repository.search(querier=querier)

        assert len(result.items) == limit
        assert result.total_count == len(sample_preset_ids)

    @pytest.mark.asyncio
    async def test_update(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        updated_name = "updated_preset"
        updated_metric_name = "new_metric"

        updater_spec = PrometheusQueryPresetUpdaterSpec(
            name=OptionalState[str].update(updated_name),
            metric_name=OptionalState[str].update(updated_metric_name),
            time_window=TriState[str].nullify(),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_preset_id)

        result = await preset_repository.update(updater=updater)

        assert result.name == updated_name
        assert result.metric_name == updated_metric_name
        assert result.time_window is None

    @pytest.mark.asyncio
    async def test_update_filter_labels_only_preserves_group_labels(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        original = await preset_repository.get_by_id(sample_preset_id)

        updated_filter_labels = ["updated_filter"]
        updater_spec = PrometheusQueryPresetUpdaterSpec(
            filter_labels=OptionalState[list[str]].update(updated_filter_labels),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_preset_id)

        result = await preset_repository.update(updater=updater)

        assert result.filter_labels == updated_filter_labels
        assert result.group_labels == original.group_labels

    @pytest.mark.asyncio
    async def test_update_group_labels_only_preserves_filter_labels(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        original = await preset_repository.get_by_id(sample_preset_id)

        updated_group_labels = ["updated_group"]
        updater_spec = PrometheusQueryPresetUpdaterSpec(
            group_labels=OptionalState[list[str]].update(updated_group_labels),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_preset_id)

        result = await preset_repository.update(updater=updater)

        assert result.group_labels == updated_group_labels
        assert result.filter_labels == original.filter_labels

    @pytest.mark.asyncio
    async def test_delete(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        deleted = await preset_repository.delete(sample_preset_id)
        assert deleted is True

        with pytest.raises(PrometheusQueryPresetNotFound):
            await preset_repository.get_by_id(sample_preset_id)

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self,
        preset_repository: PrometheusQueryPresetRepository,
    ) -> None:
        result = await preset_repository.delete(uuid.uuid4())
        assert result is False
