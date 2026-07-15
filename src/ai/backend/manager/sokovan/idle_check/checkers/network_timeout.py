from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import override

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
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


@dataclass(frozen=True)
class _NetworkIdleState:
    last_access: Decimal | None
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
                    "Network timeout checker {} has mismatched spec type: {}",
                    assignment.definition.checker_id,
                    assignment.definition.spec.type,
                )
                continue
            # Skip sessions with no timeout configured (0 means "never idle").
            if network_spec.idle_timeout_seconds == 0:
                continue
            idle_timeout_seconds = Decimal(network_spec.idle_timeout_seconds)
            for session in assignment.sessions:
                state = states[session.session_id]
                if state.last_access is None:
                    continue
                current_time = Decimal(str(context.current_time.timestamp()))
                idle_seconds = (current_time - state.last_access).normalize()
                is_idle = (state.active_connections == 0) and (idle_seconds >= idle_timeout_seconds)
                last_access_at = datetime.fromtimestamp(float(state.last_access), tz=UTC)
                judgments.append(
                    IdleJudgment(
                        checker_id=assignment.definition.checker_id,
                        session_id=session.session_id,
                        is_idle=is_idle,
                        message=(
                            "Network timeout exceeded: "
                            f"idle_timeout_seconds={idle_timeout_seconds:f}, "
                            f"last_access_at={last_access_at:%Y-%m-%d %H:%M:%S} UTC, "
                            f"idle_seconds={idle_seconds:f} "
                        ),
                    )
                )
        return judgments

    async def _prepare_states(
        self,
        sessions: Sequence[IdleCheckSession],
    ) -> dict[SessionId, _NetworkIdleState]:
        session_ids = list(dict.fromkeys(session.session_id for session in sessions))
        last_access_values, active_connection_counts = await asyncio.gather(
            self._valkey_live.get_multiple_live_data([
                f"session.{session_id}.last_access" for session_id in session_ids
            ]),
            self._valkey_live.count_active_connections_batch([
                str(session_id) for session_id in session_ids
            ]),
        )
        states: dict[SessionId, _NetworkIdleState] = {}
        for session_id, raw_last_access in zip(
            session_ids,
            last_access_values,
            strict=True,
        ):
            if raw_last_access is None or raw_last_access == b"0":
                last_access = None
            else:
                last_access = Decimal(raw_last_access.decode("utf-8"))
            states[session_id] = _NetworkIdleState(
                last_access=last_access,
                active_connections=active_connection_counts[str(session_id)],
            )
        return states
