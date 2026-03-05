from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.api.gql_legacy.agent import (
    _resolve_gpu_alloc_map,
)


class TestResolveGpuAllocMap:
    @pytest.fixture
    def mock_ctx(self) -> MagicMock:
        ctx = MagicMock()
        ctx.valkey_stat.get_gpu_allocation_map = AsyncMock(
            return_value={
                "GPU-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee": 0.5,
                "GPU-11111111-2222-3333-4444-555555555555": 1.0,
            }
        )
        return ctx

    async def test_gpu_prefixed_keys_are_resolved_as_valid_uuids(self, mock_ctx: MagicMock) -> None:
        result = await _resolve_gpu_alloc_map(mock_ctx, AgentId("i-test"))
        assert result == {
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee": 0.5,
            "11111111-2222-3333-4444-555555555555": 1.0,
        }
