from collections import defaultdict
from decimal import Decimal
from typing import Optional, Sequence

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.scheduler.policies.policy import SchedulerPolicy


class DRFPolicy(SchedulerPolicy):
    """
    Dominant Resource Fairness scheduling policy.

    This policy tries to achieve fairness by allocating resources to users
    who have the smallest dominant share of resources.
    """

    def __init__(self):
        self.per_user_dominant_share: dict[AccessKey, Decimal] = defaultdict(lambda: Decimal(0))
        self.total_capacity: Optional[ResourceSlot] = None

    @property
    def name(self) -> str:
        return "drf"

    async def apply(self) -> None:
        """Apply DRF policy - no preprocessing needed."""
        pass

    def calculate_dominant_shares(
        self,
        existing_sessions: Sequence[SessionData],
        total_capacity: ResourceSlot,
    ) -> None:
        """Calculate the initial dominant shares of all users."""
        self.total_capacity = total_capacity

        for session in existing_sessions:
            dominant_share = Decimal(0)
            self.total_capacity.sync_keys(session.occupying_slots)

            for slot, value in session.occupying_slots.items():
                slot_cap = Decimal(self.total_capacity[slot])
                if slot_cap == 0:
                    continue

                slot_share = Decimal(value) / slot_cap
                if dominant_share < slot_share:
                    dominant_share = slot_share

            access_key = session.access_key
            if access_key is not None and self.per_user_dominant_share[access_key] < dominant_share:
                self.per_user_dominant_share[access_key] = dominant_share

    def pick_session(
        self,
        pending_sessions: Sequence[SessionData],
        existing_sessions: Sequence[SessionData] | None = None,
        total_capacity: ResourceSlot | None = None,
    ) -> Optional[SessionId]:
        """
        Pick a session from the user with the lowest dominant share.

        Args:
            pending_sessions: List of pending sessions
            existing_sessions: List of existing sessions (for calculating dominant shares)
            total_capacity: Total available capacity in the system
        """
        if not pending_sessions:
            return None

        # Calculate dominant shares if provided
        if existing_sessions is not None and total_capacity is not None:
            self.calculate_dominant_shares(existing_sessions, total_capacity)

        # Find unique users with pending sessions
        users_with_pending_sessions: set[AccessKey] = {
            session.access_key for session in pending_sessions if session.access_key is not None
        }

        if not users_with_pending_sessions:
            return None

        # Find the user with the least dominant share
        least_dominant_share_user, _ = min(
            (
                (access_key, self.per_user_dominant_share[access_key])
                for access_key in users_with_pending_sessions
            ),
            key=lambda item: item[1],
        )

        # Pick the first pending session from that user
        for session in pending_sessions:
            if session.access_key is not None and session.access_key == least_dominant_share_user:
                return SessionId(session.id)

        return None

    def update_allocation(
        self,
        session: SessionData,
    ) -> None:
        """
        Update the dominant share after a session has been allocated.

        This is called after a session is successfully scheduled to update
        the internal state for the next scheduling decision.
        """
        if self.total_capacity is None:
            return

        access_key = session.access_key
        if access_key is None:
            return

        requested_slots = session.requested_slots

        # Calculate the new dominant share from this allocation
        dominant_share_from_request = Decimal(0)
        self.total_capacity.sync_keys(requested_slots)

        for slot, value in requested_slots.items():
            slot_cap = Decimal(self.total_capacity[slot])
            if slot_cap == 0:
                continue

            slot_share = Decimal(value) / slot_cap
            if dominant_share_from_request < slot_share:
                dominant_share_from_request = slot_share

        # Update if this creates a new dominant share for the user
        current_share = self.per_user_dominant_share[access_key]
        new_share = current_share + dominant_share_from_request
        self.per_user_dominant_share[access_key] = new_share
