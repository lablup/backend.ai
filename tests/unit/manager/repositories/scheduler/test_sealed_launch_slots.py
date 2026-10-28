"""Tests for reading sealed-launch slot types through the scheduler DB source."""

from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.types import SlotName, SlotTypes
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource


class TestGetSealedLaunchSlotNames:
    """Tests for get_sealed_launch_slot_names."""

    @pytest.fixture
    async def sealed_slot_types(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[None, None]:
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add_all([
                ResourceSlotTypeRow(
                    slot_name="confidential.tdx",
                    slot_type=SlotTypes.UNIQUE,
                    rank=0,
                    sealed_launch=True,
                ),
                ResourceSlotTypeRow(
                    slot_name="confidential.disabled",
                    slot_type=SlotTypes.UNIQUE,
                    rank=1,
                    sealed_launch=True,
                    enabled=False,
                ),
                ResourceSlotTypeRow(slot_name="cpu", slot_type=SlotTypes.COUNT, rank=2),
            ])
            await db_sess.flush()
        yield

    @pytest.fixture
    async def no_sealed_slot_types(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[None, None]:
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type=SlotTypes.COUNT, rank=0))
            await db_sess.flush()
        yield

    @pytest.fixture
    def db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        return ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

    @pytest.mark.usefixtures("sealed_slot_types")
    async def test_returns_sealed_slot_names_even_if_disabled(
        self,
        db_source: ScheduleDBSource,
    ) -> None:
        result = await db_source.get_sealed_launch_slot_names()

        assert result == frozenset({
            SlotName("confidential.tdx"),
            SlotName("confidential.disabled"),
        })

    @pytest.mark.usefixtures("no_sealed_slot_types")
    async def test_returns_empty_without_sealed_slot_types(
        self,
        db_source: ScheduleDBSource,
    ) -> None:
        result = await db_source.get_sealed_launch_slot_names()

        assert result == frozenset()
