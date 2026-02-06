"""GraphQL types for session management."""

from __future__ import annotations

from .fetcher import fetch_session, fetch_sessions
from .resolver import admin_sessions_v2, session_v2
from .types import (
    SessionConnectionV2GQL,
    SessionEdgeGQL,
    SessionFilterGQL,
    SessionIdentityInfoGQL,
    SessionLifecycleInfoGQL,
    SessionMetadataInfoGQL,
    SessionNetworkInfoGQL,
    SessionOrderByGQL,
    SessionOrderFieldGQL,
    SessionResourceInfoGQL,
    SessionStatusFilterGQL,
    SessionStatusGQL,
    SessionV2GQL,
)

__all__ = [
    # Fetchers
    "fetch_session",
    "fetch_sessions",
    # Resolvers
    "session_v2",
    "admin_sessions_v2",
    # V2 types
    "SessionConnectionV2GQL",
    "SessionEdgeGQL",
    "SessionFilterGQL",
    "SessionIdentityInfoGQL",
    "SessionLifecycleInfoGQL",
    "SessionMetadataInfoGQL",
    "SessionNetworkInfoGQL",
    "SessionOrderByGQL",
    "SessionOrderFieldGQL",
    "SessionResourceInfoGQL",
    "SessionStatusFilterGQL",
    "SessionStatusGQL",
    "SessionV2GQL",
]
