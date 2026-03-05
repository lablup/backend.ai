from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.models.gql_models.agent import (
    _resolve_gpu_alloc_map,
)


class TestResolveGpuAllocMap:
    @pytest.fixture
    def mock_ctx(self) -> MagicMock:
        ctx = MagicMock()
        ctx.redis_stat = MagicMock()
        return ctx

    async def test_gpu_prefixed_keys_are_resolved_as_valid_uuids(self, mock_ctx: MagicMock) -> None:
        from ai.backend.common.json import dump_json_str

        raw_data = {
            "GPU-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee": 0.5,
            "GPU-11111111-2222-3333-4444-555555555555": 1.0,
        }

        with patch(
            "ai.backend.manager.models.gql_models.agent.redis_helper.execute",
            new_callable=AsyncMock,
            return_value=dump_json_str(raw_data).encode(),
        ):
            result = await _resolve_gpu_alloc_map(mock_ctx, AgentId("i-test"))
            assert result == {
                "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee": 0.5,
                "11111111-2222-3333-4444-555555555555": 1.0,
            }
