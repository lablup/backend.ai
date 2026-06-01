from __future__ import annotations

from collections.abc import Iterator
from contextlib import AsyncExitStack
from unittest.mock import patch

import pytest

from ai.backend.web.clients.endpoint_pool.strategy import (
    EndpointSelectionPolicy,
    LeastConnectionsStrategy,
    RandomStrategy,
    RoundRobinStrategy,
    build_endpoint_selection_strategy,
)
from ai.backend.web.clients.endpoint_pool.types import EndpointEntry


def _entries(*urls: str) -> list[EndpointEntry]:
    return [EndpointEntry(endpoint=url) for url in urls]


class TestRoundRobinStrategy:
    async def test_first_pick_is_first_entry(self) -> None:
        strategy = RoundRobinStrategy()
        async with strategy.acquire(_entries("a", "b", "c")) as entry:
            assert entry.endpoint == "a"

    async def test_rotates_through_all_entries(self) -> None:
        strategy = RoundRobinStrategy()
        picks: list[str] = []
        for _ in range(6):
            async with strategy.acquire(_entries("a", "b", "c")) as entry:
                picks.append(entry.endpoint)
        assert picks == ["a", "b", "c", "a", "b", "c"]

    async def test_adapts_to_shrinking_healthy_set(self) -> None:
        strategy = RoundRobinStrategy()
        async with strategy.acquire(_entries("a", "b", "c")) as entry:
            assert entry.endpoint == "a"
        async with strategy.acquire(_entries("a", "b", "c")) as entry:
            assert entry.endpoint == "b"

        picks: list[str] = []
        for _ in range(4):
            async with strategy.acquire(_entries("a", "b")) as entry:
                picks.append(entry.endpoint)
        assert picks == ["a", "b", "a", "b"]


class TestRandomStrategy:
    async def test_acquire_picks_from_healthy_set(self) -> None:
        strategy = RandomStrategy()

        def picker(seq: list[EndpointEntry]) -> EndpointEntry:
            return seq[1]

        with patch(
            "ai.backend.web.clients.endpoint_pool.strategy.random.choice",
            side_effect=picker,
        ):
            async with strategy.acquire(_entries("a", "b", "c")) as entry:
                assert entry.endpoint == "b"


class TestLeastConnectionsStrategy:
    async def test_acquire_prefers_zero_in_flight(self) -> None:
        strategy = LeastConnectionsStrategy()
        async with AsyncExitStack() as stack:
            first = await stack.enter_async_context(strategy.acquire(_entries("a", "b", "c")))
            second = await stack.enter_async_context(strategy.acquire(_entries("a", "b", "c")))
            third = await stack.enter_async_context(strategy.acquire(_entries("a", "b", "c")))
            # Tie-break by first occurrence: a, b, c each get one.
            assert {first.endpoint, second.endpoint, third.endpoint} == {"a", "b", "c"}

    async def test_release_on_exit_decrements_counter(self) -> None:
        strategy = LeastConnectionsStrategy()
        async with strategy.acquire(_entries("a")):
            assert strategy.in_flight_count("a") == 1
            async with strategy.acquire(_entries("a")):
                assert strategy.in_flight_count("a") == 2
            assert strategy.in_flight_count("a") == 1
        assert strategy.in_flight_count("a") == 0

    async def test_release_runs_even_on_exception(self) -> None:
        strategy = LeastConnectionsStrategy()
        with pytest.raises(RuntimeError, match="boom"):
            async with strategy.acquire(_entries("a")):
                assert strategy.in_flight_count("a") == 1
                raise RuntimeError("boom")
        assert strategy.in_flight_count("a") == 0

    async def test_tie_break_by_first_occurrence(self) -> None:
        strategy = LeastConnectionsStrategy()
        async with strategy.acquire(_entries("a", "b", "c")) as entry:
            assert entry.endpoint == "a"
        # All zero again; first occurrence wins.
        async with strategy.acquire(_entries("b", "c", "a")) as entry:
            assert entry.endpoint == "b"

    async def test_acquire_picks_recovered_endpoint_when_others_busy(self) -> None:
        strategy = LeastConnectionsStrategy()
        async with AsyncExitStack() as stack:
            for _ in range(3):
                await stack.enter_async_context(strategy.acquire(_entries("a", "b")))
            # "c" comes back healthy with 0 in-flight; it should win.
            recovered = await stack.enter_async_context(
                strategy.acquire(_entries("a", "b", "c")),
            )
            assert recovered.endpoint == "c"


class TestBuildEndpointSelectionStrategy:
    @pytest.fixture(params=list(EndpointSelectionPolicy))
    def policy(self, request: pytest.FixtureRequest) -> Iterator[EndpointSelectionPolicy]:
        yield request.param

    def test_builds_concrete_strategy_for_each_policy(
        self, policy: EndpointSelectionPolicy
    ) -> None:
        strategy = build_endpoint_selection_strategy(policy)
        match policy:
            case EndpointSelectionPolicy.ROUND_ROBIN:
                assert isinstance(strategy, RoundRobinStrategy)
            case EndpointSelectionPolicy.RANDOM:
                assert isinstance(strategy, RandomStrategy)
            case EndpointSelectionPolicy.LEAST_CONNECTIONS:
                assert isinstance(strategy, LeastConnectionsStrategy)
