"""Readiness checker via appproxy."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import aiohttp

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.deployment import DeploymentRepository

from .types import ReadinessCheckResult

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ReadinessChecker:
    """Check readiness of replicas via appproxy health endpoints."""

    _repository: DeploymentRepository
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        repository: DeploymentRepository,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._repository = repository
        self._config_provider = config_provider

    async def check_readiness(
        self,
        endpoint_id: UUID,
    ) -> ReadinessCheckResult:
        """
        Check readiness of all replicas for an endpoint via appproxy.

        :param endpoint_id: ID of the endpoint to check
        :return: Readiness check result
        """
        try:
            # Get all replicas for the endpoint
            replicas = await self._repository.get_endpoint_replicas(endpoint_id)

            ready_replicas = []
            not_ready_replicas = []
            unknown_replicas = []
            check_details = {}

            # Check each replica's readiness
            check_tasks = []
            for replica in replicas:
                check_tasks.append(self._check_replica_readiness(replica.id, replica.session_id))

            # Run checks concurrently
            results = await asyncio.gather(*check_tasks, return_exceptions=True)

            # Process results
            for replica, result in zip(replicas, results):
                if isinstance(result, Exception):
                    unknown_replicas.append(replica.id)
                    check_details[replica.id] = str(result)
                elif result:
                    ready_replicas.append(replica.id)
                    check_details[replica.id] = "ready"
                else:
                    not_ready_replicas.append(replica.id)
                    check_details[replica.id] = "not_ready"

            result = ReadinessCheckResult(
                endpoint_id=endpoint_id,
                ready_replicas=ready_replicas,
                not_ready_replicas=not_ready_replicas,
                unknown_replicas=unknown_replicas,
                timestamp=datetime.now(timezone.utc),
                check_details=check_details,
            )

            log.debug(
                "Readiness check for endpoint {}: ready={}, not_ready={}, unknown={}",
                endpoint_id,
                len(ready_replicas),
                len(not_ready_replicas),
                len(unknown_replicas),
            )

            return result

        except Exception as e:
            log.error(
                "Failed to check readiness for endpoint {}: {}",
                endpoint_id,
                str(e),
            )
            # Return empty result on error
            return ReadinessCheckResult(
                endpoint_id=endpoint_id,
                ready_replicas=[],
                not_ready_replicas=[],
                unknown_replicas=[],
                timestamp=datetime.now(timezone.utc),
            )

    async def _check_replica_readiness(
        self,
        replica_id: UUID,
        session_id: UUID,
    ) -> bool:
        """
        Check readiness of a single replica.

        :param replica_id: ID of the replica
        :param session_id: ID of the session
        :return: True if ready, False otherwise
        """
        try:
            # Get appproxy endpoint for the session
            appproxy_url = await self._get_appproxy_url(session_id)
            if not appproxy_url:
                return False

            # Perform health check
            health_endpoint = f"{appproxy_url}/health"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    health_endpoint,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    # Consider 200-299 status codes as healthy
                    if 200 <= response.status < 300:
                        return True
                    else:
                        log.debug(
                            "Replica {} health check returned status {}",
                            replica_id,
                            response.status,
                        )
                        return False

        except asyncio.TimeoutError:
            log.debug("Replica {} health check timed out", replica_id)
            return False
        except Exception as e:
            log.debug(
                "Replica {} health check failed: {}",
                replica_id,
                str(e),
            )
            return False

    async def _get_appproxy_url(
        self,
        session_id: UUID,
    ) -> Optional[str]:
        """
        Get appproxy URL for a session.

        :param session_id: ID of the session
        :return: Appproxy URL or None
        """
        try:
            # Get session's appproxy endpoint from repository
            session_data = await self._repository.get_session_appproxy_endpoint(session_id)
            if session_data and session_data.appproxy_url:
                return session_data.appproxy_url

            # Fallback to constructing URL from configuration
            config = self._config_provider.config
            if hasattr(config, "appproxy") and hasattr(config.appproxy, "base_url"):
                base_url = config.appproxy.base_url
                return f"{base_url}/session/{session_id}"

            return None

        except Exception as e:
            log.error(
                "Failed to get appproxy URL for session {}: {}",
                session_id,
                str(e),
            )
            return None
