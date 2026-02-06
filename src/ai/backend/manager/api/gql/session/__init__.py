"""GraphQL types for session management."""

from __future__ import annotations

# Re-export from session_legacy.py (in parent directory) for backward compatibility
from ai.backend.manager.api.gql.session_legacy import Session

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
    # Legacy
    "Session",
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
