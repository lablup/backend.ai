from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    IdleCheckerSpecInputDTO,
    SessionLifetimeSpecInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.types import IdleCheckerInputTypeDTO
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionTypes
from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.services.idle_checker.actions.admin_search import (
    SearchIdleCheckersActionResult,
)


class TestIdleCheckerAdapter:
    @pytest.fixture
    def session_lifetime_spec_input(self) -> IdleCheckerSpecInputDTO:
        return IdleCheckerSpecInputDTO(
            session_lifetime=SessionLifetimeSpecInputDTO(max_lifetime_seconds=3600)
        )

    @pytest.fixture
    def idle_checker_data(self) -> list[IdleCheckerData]:
        timestamp = datetime(2026, 1, 1, tzinfo=UTC)
        return [
            IdleCheckerData(
                id=IdleCheckerID(uuid4()),
                name=name,
                description=None,
                checker_type=CheckerType.SESSION_LIFETIME,
                target_session_types=[SessionTypes.INTERACTIVE],
                initial_grace_period_seconds=0,
                spec=IdleCheckerSpec(
                    type=CheckerType.SESSION_LIFETIME,
                    session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=max_lifetime_seconds),
                ),
                created_at=timestamp,
                updated_at=timestamp,
            )
            for name, max_lifetime_seconds in [
                ("first", 3600),
                ("second", 7200),
            ]
        ]

    @pytest.fixture
    def missing_checker_id(self) -> IdleCheckerID:
        return IdleCheckerID(uuid4())

    @pytest.fixture
    def mock_processors(self, idle_checker_data: list[IdleCheckerData]) -> MagicMock:
        processors = MagicMock()
        processors.idle_checker.admin_search.wait_for_complete = AsyncMock(
            return_value=SearchIdleCheckersActionResult(
                items=list(reversed(idle_checker_data)),
                total_count=len(idle_checker_data),
                has_next_page=False,
                has_previous_page=False,
            )
        )
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> IdleCheckerAdapter:
        return IdleCheckerAdapter(mock_processors)

    def test_builds_session_lifetime_spec(
        self,
        adapter: IdleCheckerAdapter,
        session_lifetime_spec_input: IdleCheckerSpecInputDTO,
    ) -> None:
        spec = adapter._build_spec(
            IdleCheckerInputTypeDTO.SESSION_LIFETIME,
            session_lifetime_spec_input,
        )

        assert spec.type == CheckerType.SESSION_LIFETIME
        assert spec.session_lifetime is not None
        assert spec.session_lifetime.max_lifetime_seconds == 3600

    async def test_batch_load_preserves_input_order_and_missing_entries(
        self,
        adapter: IdleCheckerAdapter,
        idle_checker_data: list[IdleCheckerData],
        missing_checker_id: IdleCheckerID,
    ) -> None:
        requested_ids = [
            idle_checker_data[0].id,
            missing_checker_id,
            idle_checker_data[1].id,
        ]

        nodes = await adapter.batch_load_by_ids(requested_ids)

        assert [node.id if node is not None else None for node in nodes] == [
            idle_checker_data[0].id,
            None,
            idle_checker_data[1].id,
        ]
