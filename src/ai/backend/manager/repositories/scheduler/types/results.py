"""Result types for scheduling operations."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import AccessKey, SessionId


@dataclass
class ScheduledSessionData:
    """Data for a scheduled session."""

    session_id: SessionId
    creation_id: str
    # Resolved main_access_key of the owner; required for keypair-scoped concurrency tracking and resource policy lookups.
    access_key: AccessKey
    reason: str
