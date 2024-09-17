from __future__ import annotations

from collections.abc import Sequence
from typing import (
    Optional,
    override,
)

import trafaret as t

from ai.backend.common.types import (
    ResourceSlot,
    SessionId,
)

from ..models import KernelRow, SessionRow
from .types import AbstractScheduler


class FIFOSlotScheduler(AbstractScheduler):
    @property
    @override
    def config_iv(self) -> t.Dict:
        return t.Dict({
            t.Key("num_retries_to_skip", default=0): t.ToInt(gte=0),
        }).allow_extra("*")

    @override
    def pick_session(
        self,
        total_capacity: ResourceSlot,
        pending_sessions: Sequence[SessionRow],
        existing_sessions: Sequence[SessionRow],
    ) -> Optional[SessionId]:
        local_pending_sessions = list(pending_sessions)
        skipped_sessions: list[SessionRow] = []
        max_retries = self.config["num_retries_to_skip"]
        while local_pending_sessions:
            # This is the HoL blocking avoidance mechanism.
            # Just pick the first pending session, but skip it
            # if it has more than 3 failures.
            s = local_pending_sessions.pop(0)
            if max_retries == 0:  # it's strict FIFO
                return s.id
            if s.status_data is not None:
                sched_data = s.status_data.get("scheduler", {})
                if sched_data.get("retries", 0) >= max_retries:
                    skipped_sessions.append(s)
                    continue
            return s.id
        # But if all sessions are skipped, then choose the first one.
        if skipped_sessions:
            return skipped_sessions[0].id
        return None

    @override
    def update_allocation(
        self,
        scheduled_session_or_kernel: SessionRow | KernelRow,
    ) -> None:
        pass


class LIFOSlotScheduler(AbstractScheduler):
    @property
    @override
    def config_iv(self) -> t.Dict:
        return t.Dict({}).allow_extra("*")

    @override
    def pick_session(
        self,
        total_capacity: ResourceSlot,
        pending_sessions: Sequence[SessionRow],
        existing_sessions: Sequence[SessionRow],
    ) -> Optional[SessionId]:
        # Just pick the last pending session.
        return SessionId(pending_sessions[-1].id)

    @override
    def update_allocation(
        self,
        scheduled_session_or_kernel: SessionRow | KernelRow,
    ) -> None:
        pass
