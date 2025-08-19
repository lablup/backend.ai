"""Checker for route-session synchronization."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.deployment import DeploymentRepository

from .types import SyncCheckResult

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SyncChecker:
    """Check synchronization between routes and sessions."""

    _repository: DeploymentRepository

    def __init__(self, repository: DeploymentRepository) -> None:
        self._repository = repository

    async def check_sync(
        self,
        endpoint_id: UUID,
    ) -> SyncCheckResult:
        """
        Check synchronization between routes and sessions for an endpoint.

        :param endpoint_id: ID of the endpoint to check
        :return: Synchronization check result
        """
        try:
            # Get all routes for the endpoint
            routes = await self._repository.get_endpoint_routes(endpoint_id)

            # Get all sessions for the endpoint
            sessions = await self._repository.get_endpoint_sessions(endpoint_id)

            # Build mappings
            route_to_session = {r.id: r.session_id for r in routes if r.session_id}
            session_to_route = {s.id: None for s in sessions}

            # Find route for each session
            for route in routes:
                if route.session_id and route.session_id in session_to_route:
                    session_to_route[route.session_id] = route.id

            # Identify synced routes (routes with valid sessions)
            synced_routes = []
            out_of_sync_routes = []
            orphaned_routes = []

            for route in routes:
                if route.session_id:
                    # Route has a session ID
                    if route.session_id in session_to_route:
                        # Session exists
                        synced_routes.append(route.id)
                    else:
                        # Session doesn't exist (orphaned route)
                        orphaned_routes.append(route.id)
                else:
                    # Route without session (may be provisioning)
                    out_of_sync_routes.append(route.id)

            # Identify orphaned sessions (sessions without routes)
            orphaned_sessions = [
                session_id for session_id, route_id in session_to_route.items() if route_id is None
            ]

            result = SyncCheckResult(
                endpoint_id=endpoint_id,
                synced_routes=synced_routes,
                out_of_sync_routes=out_of_sync_routes,
                orphaned_routes=orphaned_routes,
                orphaned_sessions=orphaned_sessions,
                timestamp=datetime.now(timezone.utc),
            )

            log.debug(
                "Sync check for endpoint {}: synced={}, out_of_sync={}, orphaned_routes={}, orphaned_sessions={}",
                endpoint_id,
                len(synced_routes),
                len(out_of_sync_routes),
                len(orphaned_routes),
                len(orphaned_sessions),
            )

            return result

        except Exception as e:
            log.error(
                "Failed to check sync for endpoint {}: {}",
                endpoint_id,
                str(e),
            )
            # Return empty result on error
            return SyncCheckResult(
                endpoint_id=endpoint_id,
                synced_routes=[],
                out_of_sync_routes=[],
                orphaned_routes=[],
                orphaned_sessions=[],
                timestamp=datetime.now(timezone.utc),
            )
