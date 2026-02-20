"""GraphQL types for session management."""

from __future__ import annotations

from .fetcher import fetch_sessions
from .resolver import admin_sessions_v2
from .types import (
    SessionV2ConnectionGQL,
    SessionV2EdgeGQL,
    SessionV2FilterGQL,
    SessionV2GQL,
    SessionV2LifecycleInfoGQL,
    SessionV2MetadataInfoGQL,
    SessionV2NetworkInfoGQL,
    SessionV2OrderByGQL,
    SessionV2OrderFieldGQL,
    SessionV2ResourceInfoGQL,
    SessionV2RuntimeInfoGQL,
    SessionV2StatusFilterGQL,
    SessionV2StatusGQL,
)

__all__ = [
    # Fetchers
    "fetch_sessions",
    # Resolvers
    "admin_sessions_v2",
    # V2 types
    "SessionV2ConnectionGQL",
    "SessionV2EdgeGQL",
    "SessionV2FilterGQL",
    "SessionV2LifecycleInfoGQL",
    "SessionV2MetadataInfoGQL",
    "SessionV2NetworkInfoGQL",
    "SessionV2OrderByGQL",
    "SessionV2OrderFieldGQL",
    "SessionV2ResourceInfoGQL",
    "SessionV2RuntimeInfoGQL",
    "SessionV2StatusFilterGQL",
    "SessionV2StatusGQL",
    "SessionV2GQL",
]
