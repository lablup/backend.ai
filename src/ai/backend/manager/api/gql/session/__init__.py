"""GraphQL types for session management."""

from __future__ import annotations

from .fetcher import fetch_session, fetch_sessions
from .resolver import admin_sessions_v2
from .types import (
    SessionConnectionV2GQL,
    SessionV2EdgeGQL,
    SessionV2FilterGQL,
    SessionV2GQL,
    SessionV2LifecycleInfoGQL,
    SessionV2MetadataInfoGQL,
    SessionV2NetworkInfoGQL,
    SessionV2OrderByGQL,
    SessionV2OrderFieldGQL,
    SessionV2ResourceInfoGQL,
    SessionV2StatusFilterGQL,
    SessionV2StatusGQL,
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
    "SessionV2EdgeGQL",
    "SessionV2FilterGQL",
    "SessionV2LifecycleInfoGQL",
    "SessionV2MetadataInfoGQL",
    "SessionV2NetworkInfoGQL",
    "SessionV2OrderByGQL",
    "SessionV2OrderFieldGQL",
    "SessionV2ResourceInfoGQL",
    "SessionV2StatusFilterGQL",
    "SessionV2StatusGQL",
    "SessionV2GQL",
]
