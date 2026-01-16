"""GraphQL types for session management."""

from __future__ import annotations

# Re-export from session.py (in parent directory) for backward compatibility
from ai.backend.manager.api.gql.session_legacy import Session

from .fetcher import fetch_session, fetch_sessions
from .resolver import session_v2, sessions_v2
from .types import (
    SessionConnectionV2GQL,
    SessionEdgeGQL,
    SessionExecutionInfoGQL,
    SessionFilterGQL,
    SessionIdentityInfoGQL,
    SessionImageInfoGQL,
    SessionLifecycleInfoGQL,
    SessionMetadataInfoGQL,
    SessionMetricsInfoGQL,
    SessionMountInfoGQL,
    SessionNetworkInfoGQL,
    SessionOrderByGQL,
    SessionOrderFieldGQL,
    SessionResourceInfoGQL,
    SessionStatEntryGQL,
    SessionStatGQL,
    SessionStatusDataContainerGQL,
    SessionStatusFilterGQL,
    SessionStatusGQL,
    SessionStatusHistoryEntryGQL,
    SessionStatusHistoryGQL,
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
    "sessions_v2",
    # V2 types
    "SessionConnectionV2GQL",
    "SessionEdgeGQL",
    "SessionExecutionInfoGQL",
    "SessionFilterGQL",
    "SessionIdentityInfoGQL",
    "SessionImageInfoGQL",
    "SessionLifecycleInfoGQL",
    "SessionMetadataInfoGQL",
    "SessionMetricsInfoGQL",
    "SessionMountInfoGQL",
    "SessionNetworkInfoGQL",
    "SessionOrderByGQL",
    "SessionOrderFieldGQL",
    "SessionResourceInfoGQL",
    "SessionStatEntryGQL",
    "SessionStatGQL",
    "SessionStatusDataContainerGQL",
    "SessionStatusFilterGQL",
    "SessionStatusGQL",
    "SessionStatusHistoryEntryGQL",
    "SessionStatusHistoryGQL",
    "SessionV2GQL",
]
