"""The kernel live stat in the v2 GraphQL schema."""

from __future__ import annotations

from ai.backend.manager.api.gql.schema import schema


class TestKernelLiveStatSchema:
    def test_the_kernel_answers_its_live_stat(self) -> None:
        sdl = schema.as_str()

        assert "liveStat: KernelV2LiveStat\n" in sdl
        assert "type KernelV2LiveStat " in sdl
        assert "type KernelV2LiveStatMetric " in sdl
