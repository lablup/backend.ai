from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Optional, override

import trafaret as t

from ai.backend.common.types import (
    AccessKey,
    ResourceSlot,
    SessionId,
)
from ai.backend.logging import BraceStyleAdapter

from ..models import KernelRow, SessionRow
from ..models.scaling_group import ScalingGroupOpts
from .types import AbstractScheduler

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.scheduler"))


class DRFScheduler(AbstractScheduler):
    per_user_dominant_share: dict[AccessKey, Decimal]
    total_capacity: ResourceSlot

    def __init__(
        self,
        sgroup_opts: ScalingGroupOpts,
        config: Mapping[str, Any],
    ) -> None:
        super().__init__(sgroup_opts, config)
        self.per_user_dominant_share = defaultdict(lambda: Decimal(0))

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
        self.total_capacity = total_capacity

        # Calculate the initial dominant shares of all users.
        for existing_sess in existing_sessions:
            dominant_share = Decimal(0)
            self.total_capacity.sync_keys(existing_sess.occupying_slots)
            for slot, value in existing_sess.occupying_slots.items():
                slot_cap = Decimal(self.total_capacity[slot])
                if slot_cap == 0:
                    continue
                slot_share = Decimal(value) / slot_cap
                if dominant_share < slot_share:
                    dominant_share = slot_share
            if self.per_user_dominant_share[existing_sess.access_key] < dominant_share:
                self.per_user_dominant_share[existing_sess.access_key] = dominant_share
        log.debug("per-user dominant share: {}", dict(self.per_user_dominant_share))

        # Find who has the least dominant share among the pending session.
        users_with_pending_session: set[AccessKey] = {
            pending_sess.access_key for pending_sess in pending_sessions
        }
        if not users_with_pending_session:
            return None
        least_dominant_share_user, dshare = min(
            ((akey, self.per_user_dominant_share[akey]) for akey in users_with_pending_session),
            key=lambda item: item[1],
        )
        log.debug("least dominant share user: {} ({})", least_dominant_share_user, dshare)

        # Pick the first pending session of the user
        # who has the lowest dominant share.
        for pending_sess in pending_sessions:
            if pending_sess.access_key == least_dominant_share_user:
                return SessionId(pending_sess.id)

        return None

    @override
    def update_allocation(
        self,
        scheduled_session_or_kernel: SessionRow | KernelRow,
    ) -> None:
        # In such case, we just skip updating self.per_user_dominant_share state
        # and the scheduler dispatcher continues to pick another session within the same scaling group.
        access_key = scheduled_session_or_kernel.access_key
        requested_slots = scheduled_session_or_kernel.requested_slots

        # Update the dominant share.
        # This is required to use to the latest dominant share information
        # when iterating over multiple pending sessions in a single scaling group.
        dominant_share_from_request = Decimal(0)
        for slot, value in requested_slots.items():
            self.total_capacity.sync_keys(requested_slots)
            slot_cap = Decimal(self.total_capacity[slot])
            if slot_cap == 0:
                continue
            slot_share = Decimal(value) / slot_cap
            if dominant_share_from_request < slot_share:
                dominant_share_from_request = slot_share
        if self.per_user_dominant_share[access_key] < dominant_share_from_request:
            self.per_user_dominant_share[access_key] = dominant_share_from_request
