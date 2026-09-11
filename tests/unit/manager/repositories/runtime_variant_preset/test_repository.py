"""Repository tests for RuntimeVariantPreset with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.conditions import (
    RuntimeVariantPresetConditions,
)
from ai.backend.manager.models.runtime_variant_preset.creators import (
    RANK_GAP,
    RuntimeVariantPresetCreator,
)
from ai.backend.manager.models.runtime_variant_preset.orders import RuntimeVariantPresetOrders
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.runtime_variant_preset.searchers import (
    RuntimeVariantPresetSearcher,
)
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.runtime_variant_preset.repository import (
    RuntimeVariantPresetRepository,
)
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            VirtualEntityRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            EntityMembershipFieldRow,
            ScopeBindingRow,
            EntityLabelRow,
            RoleRow,
            PermissionRow,
            RuntimeVariantRow,
            RuntimeVariantPresetRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def runtime_variant_id(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AsyncGenerator[uuid.UUID, None]:
    variant_id = uuid.uuid4()
    async with db_with_cleanup.begin_session() as db_sess:
        db_sess.add(
            RuntimeVariantRow(
                id=variant_id,
                name=f"test-variant-{variant_id.hex[:8]}",
                description=None,
            )
        )
        await db_sess.flush()
    yield variant_id


@pytest.fixture
def preset_ops(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> OpsRepository[RuntimeVariantPresetData]:
    return OpsRepository(V2DBOpsProvider(db_with_cleanup))


@pytest.fixture
def repository(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> RuntimeVariantPresetRepository:
    return RuntimeVariantPresetRepository(db=db_with_cleanup)


class TestRuntimeVariantPresetRepositoryFlag:
    """Tests for creating and retrieving presets with value_type='flag'."""

    async def test_create_flag_preset_and_get_by_id(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        repository: RuntimeVariantPresetRepository,
        runtime_variant_id: uuid.UUID,
    ) -> None:
        creator = RuntimeVariantPresetCreator(
            runtime_variant_id=RuntimeVariantID(runtime_variant_id),
            name="enable-verbose",
            description="Enable verbose logging",
            preset_target=PresetTarget.ARGS,
            value_type=PresetValueType.FLAG,
            default_value="true",
            key="--verbose",
            required=False,
            added_version=None,
            deprecated_version=None,
            category=None,
            display_name=None,
            ui_option=None,
        )
        created = await preset_ops.create_global_entity(creator)

        assert created.value_type == PresetValueType.FLAG
        assert created.preset_target == PresetTarget.ARGS
        assert created.key == "--verbose"

        fetched = await repository.get_by_id(created.id)
        assert fetched.value_type == PresetValueType.FLAG
        assert fetched.preset_target == PresetTarget.ARGS
        assert fetched.default_value == "true"

    async def test_rank_advances_by_gap_within_a_variant(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
    ) -> None:
        def creator_named(name: str) -> RuntimeVariantPresetCreator:
            return RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name=name,
                description=None,
                preset_target=PresetTarget.ENV,
                value_type=PresetValueType.STR,
                default_value=None,
                key=name.upper(),
                required=False,
                added_version=None,
                deprecated_version=None,
                category=None,
                display_name=None,
                ui_option=None,
            )

        first = await preset_ops.create_global_entity(creator_named("first"))
        second = await preset_ops.create_global_entity(creator_named("second"))

        assert first.rank == RANK_GAP
        assert second.rank == RANK_GAP * 2


class TestRuntimeVariantPresetVersionRange:
    """Tests for filtering presets by the runtime version they are valid at."""

    async def test_added_version_is_an_inclusive_lower_bound(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
    ) -> None:
        await preset_ops.create_global_entity(
            RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name="added-at-0-9-0",
                description=None,
                preset_target=PresetTarget.ARGS,
                value_type=PresetValueType.STR,
                default_value=None,
                key="--added",
                required=False,
                added_version="0.9.0",
                deprecated_version=None,
                category=None,
                display_name=None,
                ui_option=None,
            )
        )

        before = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("0.8.5")],
            )
        )
        at = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("0.9.0")],
            )
        )

        assert before.items == []
        assert [item.name for item in at.items] == ["added-at-0-9-0"]

    async def test_deprecated_version_is_an_exclusive_upper_bound(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
    ) -> None:
        await preset_ops.create_global_entity(
            RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name="dropped-at-0-9-0",
                description=None,
                preset_target=PresetTarget.ARGS,
                value_type=PresetValueType.STR,
                default_value=None,
                key="--dropped",
                required=False,
                added_version=None,
                deprecated_version="0.9.0",
                category=None,
                display_name=None,
                ui_option=None,
            )
        )

        before = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("0.8.5")],
            )
        )
        at = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("0.9.0")],
            )
        )

        assert [item.name for item in before.items] == ["dropped-at-0-9-0"]
        assert at.items == []

    async def test_versions_compare_numerically_not_lexicographically(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
    ) -> None:
        await preset_ops.create_global_entity(
            RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name="added-at-0-9-0",
                description=None,
                preset_target=PresetTarget.ARGS,
                value_type=PresetValueType.STR,
                default_value=None,
                key="--added",
                required=False,
                added_version="0.9.0",
                deprecated_version=None,
                category=None,
                display_name=None,
                ui_option=None,
            )
        )

        # '0.10.0' sorts before '0.9.0' as text, so a string comparison would drop this row.
        result = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("0.10.0")],
            )
        )

        assert [item.name for item in result.items] == ["added-at-0-9-0"]

    async def test_total_count_and_has_next_page_follow_the_version_filter(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
    ) -> None:
        def creator_named(name: str, added: str | None) -> RuntimeVariantPresetCreator:
            return RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name=name,
                description=None,
                preset_target=PresetTarget.ARGS,
                value_type=PresetValueType.STR,
                default_value=None,
                key=f"--{name}",
                required=False,
                added_version=added,
                deprecated_version=None,
                category=None,
                display_name=None,
                ui_option=None,
            )

        await preset_ops.create_global_entity(creator_named("old", None))
        await preset_ops.create_global_entity(creator_named("new-a", "0.9.0"))
        await preset_ops.create_global_entity(creator_named("new-b", "0.9.0"))

        # A page of one: were the filter ignored, the two later presets would still be
        # waiting and has_next_page would be True.
        result = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=1),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("0.8.0")],
            )
        )

        assert [item.name for item in result.items] == ["old"]
        assert result.total_count == 1
        assert result.has_next_page is False

    async def test_a_suffixed_version_compares_on_its_numeric_prefix(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """The API rejects a suffix, but the column keeps whatever reaches it."""
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.insert(RuntimeVariantPresetRow).values(
                    runtime_variant=runtime_variant_id,
                    name="prerelease",
                    rank=100,
                    preset_target=PresetTarget.ARGS.value,
                    value_type=PresetValueType.STR.value,
                    key="--prerelease",
                    added_version="0.9.0rc1",
                )
            )

        at_the_release = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("0.9.0")],
            )
        )
        before_it = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("0.8.9")],
            )
        )

        assert [item.name for item in at_the_release.items] == ["prerelease"]
        assert before_it.items == []

    async def test_a_bound_with_no_numeric_prefix_matches_no_version(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """An unreadable bound is not an absent one, so it must not read as unbounded."""
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.insert(RuntimeVariantPresetRow).values(
                    runtime_variant=runtime_variant_id,
                    name="unreadable",
                    rank=100,
                    preset_target=PresetTarget.ARGS.value,
                    value_type=PresetValueType.STR.value,
                    key="--unreadable",
                    added_version="abc",
                )
            )

        result = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("10.0.0")],
            )
        )

        assert result.items == []


class TestRuntimeVariantPresetVersionOrder:
    """Ordering reads a version the way the filter does, not as text."""

    async def test_added_version_orders_numerically_with_nulls_first(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
    ) -> None:
        def creator_named(name: str, added: str | None) -> RuntimeVariantPresetCreator:
            return RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name=name,
                description=None,
                preset_target=PresetTarget.ARGS,
                value_type=PresetValueType.STR,
                default_value=None,
                key=f"--{name}",
                required=False,
                added_version=added,
                deprecated_version=None,
                category=None,
                display_name=None,
                ui_option=None,
            )

        await preset_ops.create_global_entity(creator_named("at-0-10-0", "0.10.0"))
        await preset_ops.create_global_entity(creator_named("at-0-9-0", "0.9.0"))
        await preset_ops.create_global_entity(creator_named("always", None))

        result = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                orders=RuntimeVariantPresetOrders.added_version(ascending=True),
            )
        )

        # Text ordering would put '0.10.0' before '0.9.0'.
        assert [item.name for item in result.items] == ["always", "at-0-9-0", "at-0-10-0"]

    async def test_deprecated_version_sorts_a_still_offered_preset_last(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
    ) -> None:
        def creator_named(name: str, deprecated: str | None) -> RuntimeVariantPresetCreator:
            return RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name=name,
                description=None,
                preset_target=PresetTarget.ARGS,
                value_type=PresetValueType.STR,
                default_value=None,
                key=f"--{name}",
                required=False,
                added_version=None,
                deprecated_version=deprecated,
                category=None,
                display_name=None,
                ui_option=None,
            )

        await preset_ops.create_global_entity(creator_named("still-offered", None))
        await preset_ops.create_global_entity(creator_named("gone-at-0-10-0", "0.10.0"))
        await preset_ops.create_global_entity(creator_named("gone-at-0-9-0", "0.9.0"))

        result = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                orders=RuntimeVariantPresetOrders.deprecated_version(ascending=True),
            )
        )

        assert [item.name for item in result.items] == [
            "gone-at-0-9-0",
            "gone-at-0-10-0",
            "still-offered",
        ]


class TestRuntimeVariantPresetVersionSegmentCount:
    """A version is padded to three segments, so 1, 1.0 and 1.0.0 name one version."""

    async def test_a_short_bound_equals_its_zero_filled_form(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
    ) -> None:
        def creator_named(name: str, added: str) -> RuntimeVariantPresetCreator:
            return RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name=name,
                description=None,
                preset_target=PresetTarget.ARGS,
                value_type=PresetValueType.STR,
                default_value=None,
                key=f"--{name}",
                required=False,
                added_version=added,
                deprecated_version=None,
                category=None,
                display_name=None,
                ui_option=None,
            )

        await preset_ops.create_global_entity(creator_named("one-segment", "1"))
        await preset_ops.create_global_entity(creator_named("two-segments", "1.0"))
        await preset_ops.create_global_entity(creator_named("three-segments", "1.0.0"))
        await preset_ops.create_global_entity(creator_named("later", "1.0.1"))

        result = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version("1")],
            )
        )

        # '1' admits the three spellings of itself and not the version after it.
        assert sorted(item.name for item in result.items) == [
            "one-segment",
            "three-segments",
            "two-segments",
        ]

    @pytest.mark.parametrize(
        ("version", "included"),
        [
            pytest.param("0.9.9", False, id="below_the_lower_bound"),
            pytest.param("1", True, id="at_the_lower_bound_unpadded"),
            pytest.param("1.0", True, id="at_the_lower_bound"),
            pytest.param("1.0.5", True, id="inside_the_range"),
            pytest.param("1.2", True, id="inside_with_fewer_segments"),
            pytest.param("1.2.3", False, id="at_the_exclusive_upper_bound"),
            pytest.param("2", False, id="above_the_upper_bound"),
        ],
    )
    async def test_a_range_bounded_by_differing_segment_counts(
        self,
        preset_ops: OpsRepository[RuntimeVariantPresetData],
        runtime_variant_id: uuid.UUID,
        version: str,
        included: bool,
    ) -> None:
        await preset_ops.create_global_entity(
            RuntimeVariantPresetCreator(
                runtime_variant_id=RuntimeVariantID(runtime_variant_id),
                name="two-to-three",
                description=None,
                preset_target=PresetTarget.ARGS,
                value_type=PresetValueType.STR,
                default_value=None,
                key="--two-to-three",
                required=False,
                added_version="1.0",
                deprecated_version="1.2.3",
                category=None,
                display_name=None,
                ui_option=None,
            )
        )

        result = await preset_ops.search_in_global(
            RuntimeVariantPresetSearcher(
                pagination=OffsetPagination(limit=10),
                conditions=[RuntimeVariantPresetConditions.by_valid_at_version(version)],
            )
        )

        assert bool(result.items) is included
