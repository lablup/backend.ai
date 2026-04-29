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
from ai.backend.appproxy.coordinator.types import CircuitRouteUpdateItem
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    CreatedEndpointItem,
    CreateEndpointItem,
    DeletedEndpointItem,
    RegisteredRoutesItem,
    RegisterRoutesItem,
    UnregisteredRoutesItem,
    UnregisterRoutesItem,
    UpdatedRoutesItem,
    UpdateRoutesItem,
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

    async def update_routes_bulk(
        self,
        items: list[UpdateRoutesItem],
    ) -> list[UpdatedRoutesItem]:
        """Bulk-replace routing tables for many endpoints.

        Repository commits the new ``circuit.route_info`` set in a
        single transaction; this layer then fans the change out to the
        affected workers (each worker call acquires its own circuit
        lock). Worker propagation failures don't roll back the DB write,
        but we surface them as ``success=False`` so the manager retries
        on the next short cycle and converges.
        """
        if not items:
            return []
        try:
            results = await self._repository.update_routes(items)
        except Exception as exc:
            log.warning("Bulk routes update failed: {}", exc)
            return [
                UpdatedRoutesItem(
                    deployment_id=item.deployment_id,
                    success=False,
                    error=str(exc),
                )
                for item in items
            ]

        update_items = [
            CircuitRouteUpdateItem(circuit=result.circuit, old_routes=result.old_routes)
            for result in results
            if result.success and result.circuit is not None
        ]
        if update_items:
            try:
                await self._circuit_manager.update_circuit_routes_bulk(update_items)
            except Exception as exc:
                # Locks are per-circuit but the bulk propagation either
                # completes or aborts as a unit (one Traefik put_prefix
                # / one event broadcast loop). On failure the DB write
                # is already committed, so we mark every propagated
                # entry as failed and let the manager retry on the
                # next short cycle.
                log.warning("Bulk worker propagation failed: {}", exc)
                propagated_ids = {item.circuit.endpoint_id for item in update_items}
                for result in results:
                    if (
                        result.success
                        and result.circuit is not None
                        and (result.circuit.endpoint_id in propagated_ids)
                    ):
                        result.success = False
                        result.error = f"Worker propagation failed: {exc}"

        return [
            UpdatedRoutesItem(
                deployment_id=result.deployment_id,
                success=result.success,
                error=result.error,
            )
            for result in results
        ]

    async def register_routes_bulk(
        self,
        items: list[RegisterRoutesItem],
    ) -> list[RegisteredRoutesItem]:
        """Bulk-append routes to many endpoints (delta semantics).

        Repository commits the new ``circuit.route_info`` set in a
        single transaction; this layer then fans the change out to the
        affected workers. Worker propagation failures don't roll back
        the DB write, but we surface them as ``success=False`` so the
        manager retries on the next short cycle and converges.
        """
        if not items:
            return []
        try:
            results = await self._repository.register_routes(items)
        except Exception as exc:
            log.warning("Bulk routes register failed: {}", exc)
            return [
                RegisteredRoutesItem(
                    deployment_id=item.deployment_id,
                    success=False,
                    registered_route_ids=[],
                    already_registered_route_ids=[],
                    error=str(exc),
                )
                for item in items
            ]

        update_items = [
            CircuitRouteUpdateItem(circuit=result.circuit, old_routes=result.old_routes)
            for result in results
            if result.success and result.circuit is not None
        ]
        if update_items:
            try:
                await self._circuit_manager.update_circuit_routes_bulk(update_items)
            except Exception as exc:
                # Same shape as update_routes_bulk: bulk worker
                # propagation either completes or aborts as a unit, so
                # we mark every propagated entry as failed and let the
                # manager retry on the next short cycle.
                log.warning("Bulk worker propagation (register) failed: {}", exc)
                propagated_ids = {item.circuit.endpoint_id for item in update_items}
                for result in results:
                    if (
                        result.success
                        and result.circuit is not None
                        and (result.circuit.endpoint_id in propagated_ids)
                    ):
                        result.success = False
                        result.error = f"Worker propagation failed: {exc}"

        return [
            RegisteredRoutesItem(
                deployment_id=result.deployment_id,
                success=result.success,
                registered_route_ids=result.registered_route_ids,
                already_registered_route_ids=result.already_registered_route_ids,
                error=result.error,
            )
            for result in results
        ]

    async def unregister_routes_bulk(
        self,
        items: list[UnregisterRoutesItem],
    ) -> list[UnregisteredRoutesItem]:
        """Bulk-drop routes from many endpoints (delta semantics).

        Repository commits the new ``circuit.route_info`` set in a
        single transaction; this layer then fans the change out to the
        affected workers. Worker propagation failures don't roll back
        the DB write, but we surface them as ``success=False`` so the
        manager retries on the next short cycle and converges.
        """
        if not items:
            return []
        try:
            results = await self._repository.unregister_routes(items)
        except Exception as exc:
            log.warning("Bulk routes unregister failed: {}", exc)
            return [
                UnregisteredRoutesItem(
                    deployment_id=item.deployment_id,
                    success=False,
                    unregistered_route_ids=[],
                    already_absent_route_ids=[],
                    error=str(exc),
                )
                for item in items
            ]

        update_items = [
            CircuitRouteUpdateItem(circuit=result.circuit, old_routes=result.old_routes)
            for result in results
            if result.success and result.circuit is not None
        ]
        if update_items:
            try:
                await self._circuit_manager.update_circuit_routes_bulk(update_items)
            except Exception as exc:
                log.warning("Bulk worker propagation (unregister) failed: {}", exc)
                propagated_ids = {item.circuit.endpoint_id for item in update_items}
                for result in results:
                    if (
                        result.success
                        and result.circuit is not None
                        and (result.circuit.endpoint_id in propagated_ids)
                    ):
                        result.success = False
                        result.error = f"Worker propagation failed: {exc}"

        return [
            UnregisteredRoutesItem(
                deployment_id=result.deployment_id,
                success=result.success,
                unregistered_route_ids=result.unregistered_route_ids,
                already_absent_route_ids=result.already_absent_route_ids,
                error=result.error,
            )
            for result in results
        ]

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
