"""Business logic for endpoint sync / bulk sync / delete.

Repository owns the DB + transaction boundary. The service layer only
knows about the repository and the circuit manager, so it never touches
``db`` or ``execute_with_txn_retry`` directly.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import AnyUrl

from ai.backend.appproxy.coordinator.models import Circuit
from ai.backend.appproxy.coordinator.repositories.endpoint import (
    EndpointRepository,
    SyncedEndpoint,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    CreatedEndpointItem,
    CreateEndpointItem,
    DeletedEndpointItem,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.appproxy.coordinator.types import CircuitManager

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class EndpointService:
    _repository: EndpointRepository
    _circuit_manager: CircuitManager

    def __init__(
        self,
        repository: EndpointRepository,
        circuit_manager: CircuitManager,
    ) -> None:
        self._repository = repository
        self._circuit_manager = circuit_manager

    async def sync_endpoint(
        self,
        item: CreateEndpointItem,
    ) -> CreatedEndpointItem:
        """Sync a single endpoint + circuit and propagate to workers."""
        [synced] = await self._repository.sync_endpoints([item])
        await self._propagate_new_circuits([synced])
        return self._to_created_item(synced)

    async def sync_endpoints_bulk(
        self,
        items: list[CreateEndpointItem],
    ) -> list[CreatedEndpointItem]:
        """Bulk-sync many endpoints; initialize new circuits in one batch."""
        synced_list = await self._repository.sync_endpoints(items)
        await self._propagate_new_circuits(synced_list)
        return [self._to_created_item(s) for s in synced_list]

    async def delete_endpoint(self, deployment_id: DeploymentID) -> None:
        """Remove an endpoint + its circuit and unload from workers."""
        circuits = await self._repository.delete_endpoints([deployment_id])
        if circuits:
            await self._circuit_manager.unload_circuits(circuits)

    async def delete_endpoints_bulk(
        self,
        deployment_ids: list[DeploymentID],
    ) -> list[DeletedEndpointItem]:
        """Bulk-remove endpoints in a single set-based transaction.

        All input ids are attempted atomically: the repository deletes
        every row whose id is in the set and returns the affected
        circuits, which are then unloaded from workers in one batch.
        Missing ids count as success (delete is idempotent). A
        transaction-level failure is reported against every input id
        since the bulk path cannot isolate per-entry errors.
        """
        if not deployment_ids:
            return []
        try:
            circuits = await self._repository.delete_endpoints(deployment_ids)
        except Exception as exc:
            log.warning("Bulk endpoint delete failed: {}", exc)
            return [
                DeletedEndpointItem(
                    deployment_id=deployment_id,
                    success=False,
                    error=str(exc),
                )
                for deployment_id in deployment_ids
            ]
        if circuits:
            await self._circuit_manager.unload_circuits(circuits)
        return [
            DeletedEndpointItem(deployment_id=deployment_id, success=True)
            for deployment_id in deployment_ids
        ]

    async def _propagate_new_circuits(
        self,
        synced_list: list[SyncedEndpoint],
    ) -> None:
        new_circuits: list[Circuit] = [s.new_circuit for s in synced_list if s.new_circuit]
        if new_circuits:
            await self._circuit_manager.initialize_circuits(new_circuits)

    @staticmethod
    def _to_created_item(synced: SyncedEndpoint) -> CreatedEndpointItem:
        return CreatedEndpointItem(
            deployment_id=synced.deployment_id,
            url=AnyUrl(str(synced.url)),
            health_check_enabled=synced.health_check_enabled,
        )
