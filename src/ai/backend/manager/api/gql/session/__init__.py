"""GraphQL types for session management."""

from __future__ import annotations

from .fetcher import fetch_sessions
from .resolver import (
    # Mutations
    admin_modify_session,
    admin_sessions_v2,
    check_and_transit_session_status,
    commit_session,
    complete_session_code,
    convert_session_to_image,
    create_session_cluster,
    create_session_from_params,
    create_session_from_template,
    destroy_session,
    execute_in_session,
    interrupt_session,
    rename_session,
    restart_session,
    shutdown_session_service,
    start_session_service,
)
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
    SessionV2StatusFilterGQL,
    SessionV2StatusGQL,
)

__all__ = [
    # Fetchers
    "fetch_sessions",
    # Resolvers - Queries
    "admin_sessions_v2",
    # Resolvers - Mutations
    "admin_modify_session",
    "check_and_transit_session_status",
    "destroy_session",
    "restart_session",
    "rename_session",
    "interrupt_session",
    "execute_in_session",
    "commit_session",
    "convert_session_to_image",
    "start_session_service",
    "shutdown_session_service",
    "complete_session_code",
    "create_session_from_params",
    "create_session_from_template",
    "create_session_cluster",
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
    "SessionV2StatusFilterGQL",
    "SessionV2StatusGQL",
    "SessionV2GQL",
]
