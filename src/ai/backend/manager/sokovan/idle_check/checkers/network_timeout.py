from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleChecker,
    IdleCheckerContext,
    IdleJudgment,
)

log = BraceStyleAdapter(logging.getLogger(__name__))

_ONGOING_ACTIVITY_SENTINEL = 0.0


@dataclass(frozen=True)
class _NetworkIdleState:
    last_access: float | None
    active_connections: int


class NetworkTimeoutChecker(IdleChecker):
    """Judge interactive sessions from their shared network-activity markers."""

    _valkey_live: ValkeyLiveClient

    def __init__(self, valkey_live: ValkeyLiveClient) -> None:
        self._valkey_live = valkey_live

    @override
    async def judge(
        self,
        assignments: Sequence[CheckerAssignment],
        *,
        context: IdleCheckerContext,
    ) -> Sequence[IdleJudgment]:
        # Fetch session states in one batch to avoid repeated I/O per assignment.
        sessions: list[IdleCheckSession] = []
        for assignment in assignments:
            sessions.extend(assignment.sessions)
        states = await self._prepare_states(sessions)

        # Judge each assignment in one pass, using the pre-fetched states.
        judgments: list[IdleJudgment] = []
        for assignment in assignments:
            network_spec = assignment.definition.spec.network
            if network_spec is None:
                log.error(
                    "Network timeout checker has mismatched spec type - check id: {}, spec type: {}",
                    assignment.definition.checker_id,
                    assignment.definition.spec.type,
                )
                continue
            max_inactivity_seconds = network_spec.max_network_inactivity_seconds
            if max_inactivity_seconds == 0:
                continue
            for session in assignment.sessions:
                judgment = self._judge_session(
                    checker_id=assignment.definition.checker_id,
                    session_id=session.session_id,
                    expire_at=session.expire_at,
                    state=states[session.session_id],
                    max_inactivity_seconds=max_inactivity_seconds,
                    current_time=context.current_time,
                )
                if judgment is not None:
                    judgments.append(judgment)
        return judgments

    def _judge_session(
        self,
        *,
        checker_id: IdleCheckerID,
        session_id: SessionId,
        expire_at: datetime,
        state: _NetworkIdleState,
        max_inactivity_seconds: int,
        current_time: datetime,
    ) -> IdleJudgment | None:
        if state.last_access is None:
            return None
        if state.last_access == _ONGOING_ACTIVITY_SENTINEL or state.active_connections > 0:
            return IdleJudgment(
                checker_id=checker_id,
                session_id=session_id,
                expire_at=current_time + timedelta(seconds=max_inactivity_seconds),
                status=IdleCheckPhase.ACTIVE,
                message=(
                    "Network activity detected: "
                    f"max_network_inactivity_seconds={max_inactivity_seconds}, "
                    f"active_connections={state.active_connections}"
                ),
            )
        last_access_at = datetime.fromtimestamp(state.last_access, tz=UTC)
        if current_time >= expire_at:
            status = IdleCheckPhase.IDLE_EXPIRED
            message = "Maximum network inactivity exceeded"
        else:
            status = IdleCheckPhase.IDLE
            message = "No active network connection"
        return IdleJudgment(
            checker_id=checker_id,
            session_id=session_id,
            expire_at=expire_at,
            status=status,
            message=(
                f"{message}: "
                f"max_network_inactivity_seconds={max_inactivity_seconds}, "
                f"active_connections={state.active_connections}, "
                f"last_access_at={last_access_at:%Y-%m-%d %H:%M:%S} UTC, "
                f"inactive_seconds={(current_time - last_access_at).total_seconds():f}"
            ),
        )

    async def _prepare_states(
        self,
        sessions: Sequence[IdleCheckSession],
    ) -> dict[SessionId, _NetworkIdleState]:
        session_ids = list(dict.fromkeys(session.session_id for session in sessions))
        last_access_values, active_connection_counts = await asyncio.gather(
            self._valkey_live.get_multiple_live_data([
                f"session.{session_id}.last_access" for session_id in session_ids
            ]),
            self._valkey_live.count_active_connections_batch(session_ids),
        )
        states: dict[SessionId, _NetworkIdleState] = {}
        for session_id, raw_last_access in zip(
            session_ids,
            last_access_values,
            strict=True,
        ):
            if raw_last_access is None:
                last_access = None
            else:
                last_access = float(raw_last_access)
            states[session_id] = _NetworkIdleState(
                last_access=last_access,
                active_connections=active_connection_counts[session_id],
            )
        return states
