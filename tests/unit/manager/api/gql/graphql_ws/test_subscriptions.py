import asyncio
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from strawberry.types.execution import ExecutionResult, PreExecutionError

from ai.backend.manager.api.gql.graphql_ws.subscriptions import SubscriptionExecutor
from ai.backend.manager.api.gql.graphql_ws.types import (
    ClientCompleteMessage,
    GQLWSMessageType,
    SubscribeMessage,
    SubscribePayload,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sender(*, closed: bool = False) -> AsyncMock:
    sender = AsyncMock()
    type(sender).closed = PropertyMock(return_value=closed)
    return sender


def _make_gql_deps() -> MagicMock:
    deps = MagicMock()
    deps.processors.events.event_hub = MagicMock()
    deps.processors.events.event_fetcher = MagicMock()
    deps.strawberry_gql_adapter = MagicMock()
    deps.strawberry_data_loaders = MagicMock()
    deps.metric_observer = MagicMock()
    deps.adapters = MagicMock()
    deps.config_provider = MagicMock()
    return deps


def _subscribe_msg(sub_id: str = "1", query: str = "subscription { e }") -> SubscribeMessage:
    return SubscribeMessage(
        type=GQLWSMessageType.SUBSCRIBE,
        id=sub_id,
        payload=SubscribePayload(query=query),
    )


def _complete_msg(sub_id: str = "1") -> ClientCompleteMessage:
    return ClientCompleteMessage(type=GQLWSMessageType.COMPLETE, id=sub_id)


async def _async_iter_from(items: list[Any]) -> AsyncIterator[Any]:
    for item in items:
        yield item


# ===========================================================================
# SubscriptionExecutor
# ===========================================================================


class TestSubscriptionExecutor:
    """Tests for per-connection subscription management."""

    @pytest.fixture
    def mock_sender(self) -> AsyncMock:
        return _make_sender()

    @pytest.fixture
    def mock_schema(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_deps(self) -> MagicMock:
        return _make_gql_deps()

    @pytest.fixture
    def executor(
        self,
        mock_sender: AsyncMock,
        mock_schema: AsyncMock,
        mock_deps: MagicMock,
    ) -> SubscriptionExecutor:
        return SubscriptionExecutor(mock_sender, mock_schema, mock_deps)

    # -- start --------------------------------------------------------------

    async def test_start_creates_task(self, executor: SubscriptionExecutor) -> None:
        msg = _subscribe_msg("sub-1")
        await executor.start(msg)
        assert "sub-1" in executor._tasks
        await executor.cancel_all()

    async def test_start_duplicate_closes_connection(
        self, executor: SubscriptionExecutor, mock_sender: AsyncMock
    ) -> None:
        msg = _subscribe_msg("dup")
        await executor.start(msg)
        # Second start with same id
        await executor.start(msg)
        mock_sender.close_duplicate_subscriber.assert_awaited_once()
        await executor.cancel_all()

    # -- cancel -------------------------------------------------------------

    async def test_cancel_removes_task(self, executor: SubscriptionExecutor) -> None:
        msg = _subscribe_msg("c1")
        await executor.start(msg)
        assert "c1" in executor._tasks

        executor.cancel(_complete_msg("c1"))
        assert "c1" not in executor._tasks

    def test_cancel_nonexistent_is_noop(self, executor: SubscriptionExecutor) -> None:
        executor.cancel(_complete_msg("nope"))

    # -- cancel_all ---------------------------------------------------------

    async def test_cancel_all_clears_tasks(self, executor: SubscriptionExecutor) -> None:
        await executor.start(_subscribe_msg("a"))
        await executor.start(_subscribe_msg("b"))
        assert len(executor._tasks) == 2

        await executor.cancel_all()
        assert len(executor._tasks) == 0

    # -- _run: streaming ----------------------------------------------------

    async def test_run_streams_results_and_completes(
        self,
        executor: SubscriptionExecutor,
        mock_schema: AsyncMock,
        mock_sender: AsyncMock,
    ) -> None:
        result1 = MagicMock(spec=ExecutionResult)
        result1.data = {"count": 1}
        result1.errors = None
        result2 = MagicMock(spec=ExecutionResult)
        result2.data = {"count": 2}
        result2.errors = None

        mock_schema.subscribe.return_value = _async_iter_from([result1, result2])

        with patch.object(executor, "_make_gql_context", return_value=MagicMock()):
            # Run _run directly (not via start, to avoid task indirection)
            await executor._run("s1", SubscribePayload(query="{ e }"))

        assert mock_sender.send_next.await_count == 2
        mock_sender.send_complete.assert_awaited_once_with("s1")

    # -- _run: pre-execution error ------------------------------------------

    async def test_run_pre_execution_error(
        self,
        executor: SubscriptionExecutor,
        mock_schema: AsyncMock,
        mock_sender: AsyncMock,
    ) -> None:
        pre_err = MagicMock(spec=PreExecutionError)
        pre_err.errors = []

        mock_schema.subscribe.return_value = _async_iter_from([pre_err])

        with patch.object(executor, "_make_gql_context", return_value=MagicMock()):
            await executor._run("s1", SubscribePayload(query="bad"))

        mock_sender.send_pre_execution_error.assert_awaited_once()
        # complete is still sent after pre-execution error
        mock_sender.send_complete.assert_awaited_once_with("s1")

    # -- _run: unexpected exception -----------------------------------------

    async def test_run_exception_sends_internal_error(
        self,
        executor: SubscriptionExecutor,
        mock_schema: AsyncMock,
        mock_sender: AsyncMock,
    ) -> None:
        mock_schema.subscribe.side_effect = RuntimeError("boom")

        with patch.object(executor, "_make_gql_context", return_value=MagicMock()):
            await executor._run("s1", SubscribePayload(query="{ e }"))

        mock_sender.send_internal_error.assert_awaited_once_with("s1")
        mock_sender.send_complete.assert_awaited_once_with("s1")

    # -- _run: cancellation -------------------------------------------------

    async def test_run_cancellation_does_not_send_complete(
        self,
        executor: SubscriptionExecutor,
        mock_schema: AsyncMock,
        mock_sender: AsyncMock,
    ) -> None:
        started = asyncio.Event()

        async def _hang_forever() -> AsyncIterator[Any]:
            started.set()
            await asyncio.sleep(999)
            yield  # unreachable

        mock_schema.subscribe.return_value = _hang_forever()

        with patch.object(executor, "_make_gql_context", return_value=MagicMock()):
            task = asyncio.create_task(executor._run("s1", SubscribePayload(query="{ e }")))
            await started.wait()
            task.cancel()
            # _run catches CancelledError internally — task completes normally
            await task

        mock_sender.send_complete.assert_not_awaited()

    # -- _run: sender closed mid-stream -------------------------------------

    async def test_run_stops_when_sender_closed(
        self,
        executor: SubscriptionExecutor,
        mock_schema: AsyncMock,
    ) -> None:
        closed_sender = _make_sender(closed=True)
        executor._sender = closed_sender

        result = MagicMock()
        mock_schema.subscribe.return_value = _async_iter_from([result])

        with patch.object(executor, "_make_gql_context", return_value=MagicMock()):
            await executor._run("s1", SubscribePayload(query="{ e }"))

        closed_sender.send_next.assert_not_awaited()
