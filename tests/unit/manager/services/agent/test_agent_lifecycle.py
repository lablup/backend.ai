"""Unit tests for agent lifecycle, heartbeat, and watcher operations.

Tests the AgentService layer with real DB and Valkey, validating:
- Agent status transitions (ALIVE / LOST / TERMINATED / RESTARTING)
- Heartbeat processing (normal, revival, new-agent creation)
- Cache cleanup on agent exit (last_seen, image cache, RPC cache)
- Watcher start / stop / restart operations
- Redis/Valkey failure suppression via suppress_with_log
"""

from __future__ import annotations

import secrets
from collections.abc import Callable, Coroutine
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.events.event_types.agent.anycast import AgentStartedEvent
from ai.backend.common.types import AgentId, ResourceSlot, SlotName, SlotTypes
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.services.agent.actions.handle_heartbeat import HandleHeartbeatAction
from ai.backend.manager.services.agent.actions.mark_agent_exit import MarkAgentExitAction
from ai.backend.manager.services.agent.actions.mark_agent_running import MarkAgentRunningAction
from ai.backend.manager.services.agent.actions.watcher_agent_restart import (
    WatcherAgentRestartAction,
)
from ai.backend.manager.services.agent.actions.watcher_agent_start import WatcherAgentStartAction
from ai.backend.manager.services.agent.actions.watcher_agent_stop import WatcherAgentStopAction
from ai.backend.manager.services.agent.service import AgentService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent_info(scaling_group: str) -> AgentInfo:
    """Build a minimal AgentInfo for heartbeat tests."""
    return AgentInfo(
        ip="127.0.0.1",
        region="test-region",
        scaling_group=scaling_group,
        addr="http://127.0.0.1:6001",
        public_key=None,
        public_host="127.0.0.1",
        available_resource_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
        slot_key_and_units={SlotName("cpu"): SlotTypes.COUNT, SlotName("mem"): SlotTypes.BYTES},
        version="24.09.0",
        compute_plugins={},
        images=b"",
        architecture="x86_64",
        auto_terminate_abusing_kernel=False,
    )


async def _query_agent_status(db_engine: SAEngine, agent_id: AgentId) -> AgentStatus | None:
    """Query current agent status from DB."""
    async with db_engine.begin() as conn:
        result = await conn.execute(
            sa.select(AgentRow.__table__.c.status).where(AgentRow.__table__.c.id == agent_id)
        )
        row = result.first()
        if row is None:
            return None
        return AgentStatus(row[0])


async def _agent_exists(db_engine: SAEngine, agent_id: AgentId) -> bool:
    """Return True if the agent row exists in DB."""
    async with db_engine.begin() as conn:
        result = await conn.execute(
            sa.select(sa.func.count()).where(AgentRow.__table__.c.id == agent_id)
        )
        return result.scalar_one() > 0


# ---------------------------------------------------------------------------
# Status transition tests
# ---------------------------------------------------------------------------


class TestAgentLifecycleStatusTransitions:
    """Agent status transitions driven by mark_agent_exit / mark_agent_running."""

    async def test_alive_to_lost_transition(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
        db_engine: SAEngine,
    ) -> None:
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory(status=AgentStatus.ALIVE)

        await service.mark_agent_exit(
            MarkAgentExitAction(agent_id=agent_id, agent_status=AgentStatus.LOST)
        )

        assert await _query_agent_status(db_engine, agent_id) == AgentStatus.LOST

    async def test_alive_to_terminated_transition(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
        db_engine: SAEngine,
    ) -> None:
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory(status=AgentStatus.ALIVE)

        await service.mark_agent_exit(
            MarkAgentExitAction(agent_id=agent_id, agent_status=AgentStatus.TERMINATED)
        )

        assert await _query_agent_status(db_engine, agent_id) == AgentStatus.TERMINATED

    async def test_alive_to_restarting_transition(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
        db_engine: SAEngine,
    ) -> None:
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory(status=AgentStatus.ALIVE)

        await service.mark_agent_exit(
            MarkAgentExitAction(agent_id=agent_id, agent_status=AgentStatus.RESTARTING)
        )

        assert await _query_agent_status(db_engine, agent_id) == AgentStatus.RESTARTING

    async def test_mark_agent_running_updates_status(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
        db_engine: SAEngine,
    ) -> None:
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory(status=AgentStatus.LOST)

        await service.mark_agent_running(
            MarkAgentRunningAction(agent_id=agent_id, agent_status=AgentStatus.ALIVE)
        )

        assert await _query_agent_status(db_engine, agent_id) == AgentStatus.ALIVE


# ---------------------------------------------------------------------------
# Heartbeat processing tests
# ---------------------------------------------------------------------------


class TestHeartbeatProcessing:
    """Heartbeat upsert behaviour: normal, revival, and new-agent creation."""

    async def test_normal_heartbeat_keeps_agent_alive(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
        db_engine: SAEngine,
        scaling_group_fixture: str,
        resource_slot_types_seeded: None,
    ) -> None:
        service, mock_event_producer, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory(status=AgentStatus.ALIVE)
        agent_info = _make_agent_info(scaling_group_fixture)

        await service.handle_heartbeat(
            HandleHeartbeatAction(agent_id=agent_id, agent_info=agent_info)
        )

        assert await _query_agent_status(db_engine, agent_id) == AgentStatus.ALIVE
        mock_event_producer.anycast_event.assert_not_called()

    async def test_heartbeat_revives_lost_agent(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
        db_engine: SAEngine,
        scaling_group_fixture: str,
        resource_slot_types_seeded: None,
    ) -> None:
        service, mock_event_producer, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory(status=AgentStatus.LOST)
        agent_info = _make_agent_info(scaling_group_fixture)

        await service.handle_heartbeat(
            HandleHeartbeatAction(agent_id=agent_id, agent_info=agent_info)
        )

        assert await _query_agent_status(db_engine, agent_id) == AgentStatus.ALIVE
        mock_event_producer.anycast_event.assert_called_once()
        call_args = mock_event_producer.anycast_event.call_args
        assert isinstance(call_args.args[0], AgentStartedEvent)

    async def test_new_agent_heartbeat_creates_agent(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        db_engine: SAEngine,
        scaling_group_fixture: str,
        resource_slot_types_seeded: None,
    ) -> None:
        service, _, _, _ = lifecycle_agent_service
        agent_id = AgentId(f"i-new-{secrets.token_hex(4)}")
        agent_info = _make_agent_info(scaling_group_fixture)

        try:
            await service.handle_heartbeat(
                HandleHeartbeatAction(agent_id=agent_id, agent_info=agent_info)
            )

            assert await _agent_exists(db_engine, agent_id)
            assert await _query_agent_status(db_engine, agent_id) == AgentStatus.ALIVE
        finally:
            async with db_engine.begin() as conn:
                await conn.execute(
                    AgentRow.__table__.delete().where(AgentRow.__table__.c.id == agent_id)
                )


# ---------------------------------------------------------------------------
# Cache cleanup tests
# ---------------------------------------------------------------------------


class TestCacheCleanupOnAgentExit:
    """mark_agent_exit must clean up RPC cache, last_seen, and image cache."""

    async def test_exit_clears_rpc_cache(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
    ) -> None:
        service, _, _, mock_agent_cache = lifecycle_agent_service
        agent_id = await agent_row_factory()

        await service.mark_agent_exit(
            MarkAgentExitAction(agent_id=agent_id, agent_status=AgentStatus.TERMINATED)
        )

        mock_agent_cache.discard.assert_called_once_with(agent_id)

    async def test_exit_suppresses_last_seen_valkey_failure(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
    ) -> None:
        """Valkey error in remove_agent_last_seen must be suppressed, not raised."""
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory()

        with patch.object(
            service._agent_repository._cache_source,
            "remove_agent_last_seen",
            side_effect=ConnectionError("valkey unavailable"),
        ):
            # Should complete without raising despite Valkey failure
            await service.mark_agent_exit(
                MarkAgentExitAction(agent_id=agent_id, agent_status=AgentStatus.TERMINATED)
            )

    async def test_exit_suppresses_image_cache_failure(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
    ) -> None:
        """Valkey error in remove_agent_from_all_images must be suppressed, not raised."""
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory()

        with patch.object(
            service._agent_repository._cache_source,
            "remove_agent_from_all_images",
            side_effect=ConnectionError("valkey unavailable"),
        ):
            await service.mark_agent_exit(
                MarkAgentExitAction(agent_id=agent_id, agent_status=AgentStatus.TERMINATED)
            )


# ---------------------------------------------------------------------------
# Watcher operation tests
# ---------------------------------------------------------------------------


class TestWatcherOperations:
    """Watcher start / stop / restart delegate to the watcher HTTP endpoint."""

    async def test_watcher_start_succeeds(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
    ) -> None:
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory()

        mock_request = AsyncMock(return_value={"status": "started"})
        with patch.object(service, "_request_watcher", mock_request):
            result = await service.watcher_agent_start(WatcherAgentStartAction(agent_id=agent_id))

        mock_request.assert_called_once_with(
            agent_id=agent_id, method="POST", endpoint="agent/start"
        )
        assert result.data == {"status": "started"}
        assert result.agent_id == agent_id

    async def test_watcher_stop_succeeds(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
    ) -> None:
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory()

        mock_request = AsyncMock(return_value={"status": "stopped"})
        with patch.object(service, "_request_watcher", mock_request):
            result = await service.watcher_agent_stop(WatcherAgentStopAction(agent_id=agent_id))

        mock_request.assert_called_once_with(
            agent_id=agent_id, method="POST", endpoint="agent/stop"
        )
        assert result.data == {"status": "stopped"}
        assert result.agent_id == agent_id

    async def test_watcher_restart_succeeds(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
    ) -> None:
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory()

        mock_request = AsyncMock(return_value={"status": "restarted"})
        with patch.object(service, "_request_watcher", mock_request):
            result = await service.watcher_agent_restart(
                WatcherAgentRestartAction(agent_id=agent_id)
            )

        mock_request.assert_called_once_with(
            agent_id=agent_id, method="POST", endpoint="agent/restart"
        )
        assert result.data == {"status": "restarted"}
        assert result.agent_id == agent_id


# ---------------------------------------------------------------------------
# Error handling / suppress_with_log tests
# ---------------------------------------------------------------------------


class TestValkeySuppression:
    """Redis/Valkey failures during heartbeat must be suppressed, not raised."""

    async def test_heartbeat_suppresses_last_seen_valkey_failure(
        self,
        lifecycle_agent_service: tuple[AgentService, AsyncMock, AsyncMock, MagicMock],
        agent_row_factory: Callable[..., Coroutine[Any, Any, AgentId]],
        db_engine: SAEngine,
        scaling_group_fixture: str,
        resource_slot_types_seeded: None,
    ) -> None:
        """update_agent_last_seen failure in heartbeat is suppressed via suppress_with_log."""
        service, _, _, _ = lifecycle_agent_service
        agent_id = await agent_row_factory(status=AgentStatus.ALIVE)
        agent_info = _make_agent_info(scaling_group_fixture)

        with patch.object(
            service._agent_repository._cache_source,
            "update_agent_last_seen",
            side_effect=ConnectionError("valkey unavailable"),
        ):
            # Despite Valkey failure, heartbeat completes and status stays ALIVE
            await service.handle_heartbeat(
                HandleHeartbeatAction(agent_id=agent_id, agent_info=agent_info)
            )

        assert await _query_agent_status(db_engine, agent_id) == AgentStatus.ALIVE
