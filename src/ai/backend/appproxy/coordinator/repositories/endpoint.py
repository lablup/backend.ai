"""Repository layer for endpoint + circuit DB access.

Owns the DB engine and the transaction boundary. Public methods are
logical units that span one or more ORM operations inside a single
transaction so the caller (service layer) only deals with business
logic, never with ``begin_session`` plumbing.

Bulk-first: read and write queries are batched with ``IN (...)`` so
one request processing N deployments touches the DB O(phases) times
instead of O(N).

Isolation: every transaction opened here runs at READ COMMITTED to
avoid the coordinator's engine-level SERIALIZABLE default. Reads
between concurrent endpoint sync/delete flows do not need
serializable guarantees — all mutations in this module are keyed on
deployment id and any conflict surfaces as a FK/unique violation.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload
from yarl import URL

from ai.backend.appproxy.common.types import (
    AppMode,
    EndpointConfig,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
    SessionConfig,
)
from ai.backend.appproxy.coordinator.errors import InvalidURLError
from ai.backend.appproxy.coordinator.models import Circuit, Endpoint, Worker
from ai.backend.appproxy.coordinator.models.utils import ExtendedAsyncSAEngine
from ai.backend.appproxy.coordinator.models.worker import add_circuit
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    CreateEndpointItem,
    RegisterRoutesItem,
    UnregisterRoutesItem,
    UpdateRoutesItem,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(slots=True)
class SyncedEndpoint:
    """Result of a single endpoint sync within a transaction."""

    deployment_id: DeploymentID
    url: URL
    health_check_enabled: bool
    new_circuit: Circuit | None


@dataclass
class UpdatedRouteSet:
    """One endpoint's routing-table update result.

    ``circuit`` and ``old_routes`` are only populated on success so the
    service layer can fan the new route set out to workers after the
    transaction commits.
    """

    deployment_id: DeploymentID
    success: bool
    error: str | None
    circuit: Circuit | None
    old_routes: list[RouteInfo]


@dataclass
class RegisteredRouteSet:
    """One endpoint's routes-register result.

    Mirrors :class:`UpdatedRouteSet` so the service layer can fan the
    new route set out to workers using the same propagation path. The
    register / already-register split lets the caller distinguish a
    first-time push from a redundant one.
    """

    deployment_id: DeploymentID
    success: bool
    error: str | None
    circuit: Circuit | None
    old_routes: list[RouteInfo]
    registered_route_ids: list[UUID]
    already_registered_route_ids: list[UUID]


@dataclass
class UnregisteredRouteSet:
    """One endpoint's routes-unregister result.

    Mirrors :class:`UpdatedRouteSet` so the service layer can fan the
    smaller route set out to workers using the same propagation path.
    The unregister / already-absent split lets the caller distinguish a
    first-time removal from a redundant one.
    """

    deployment_id: DeploymentID
    success: bool
    error: str | None
    circuit: Circuit | None
    old_routes: list[RouteInfo]
    unregistered_route_ids: list[UUID]
    already_absent_route_ids: list[UUID]


class EndpointRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # ---- Transaction boundary (READ COMMITTED) ----

    @asynccontextmanager
    async def _begin_readonly_session_read_committed(self) -> AsyncIterator[SASession]:
        """Read-only session at READ COMMITTED isolation."""
        async with self._db.connect() as conn:
            conn_with_isolation = await conn.execution_options(
                isolation_level="READ COMMITTED",
                postgresql_readonly=True,
            )
            async with conn_with_isolation.begin():
                sess_factory = async_sessionmaker(
                    bind=conn_with_isolation,
                    expire_on_commit=False,
                )
                session = sess_factory()
                yield session

    @asynccontextmanager
    async def _begin_session_read_committed(self) -> AsyncIterator[SASession]:
        """Read-write session at READ COMMITTED isolation, auto-commit on exit."""
        async with self._db.connect() as conn:
            conn_with_isolation = await conn.execution_options(isolation_level="READ COMMITTED")
            async with conn_with_isolation.begin():
                sess_factory = async_sessionmaker(
                    bind=conn_with_isolation,
                    expire_on_commit=False,
                )
                session = sess_factory()
                yield session
                await session.commit()

    # ---- Public (transactional) API ----

    async def sync_endpoints(
        self,
        items: list[CreateEndpointItem],
    ) -> list[SyncedEndpoint]:
        """Create or sync many endpoints inside one transaction.

        Reads are batched: existing endpoints and existing circuits for
        all requested deployments are fetched in two bulk queries. New
        circuit creation stays per-item because ``add_circuit`` owns
        per-endpoint worker / port / subdomain selection.

        Returns per-item results in input order. Callers read
        ``new_circuit`` to batch-propagate freshly created circuits.
        """
        if not items:
            return []

        results: list[SyncedEndpoint] = []
        deployment_ids = [item.deployment_id for item in items]

        async with self._begin_session_read_committed() as sess:
            # Bulk-fetch existing endpoints so we can update them in place
            # without a per-item SELECT.
            endpoint_rows = (
                await sess.scalars(sa.select(Endpoint).where(Endpoint.id.in_(deployment_ids)))
            ).all()
            endpoints_by_id: dict[UUID, Endpoint] = {e.id: e for e in endpoint_rows}

            # Bulk-fetch existing circuits for the same deployments so
            # the idempotent "already wired" path is a dict lookup.
            circuit_rows = (
                await sess.scalars(
                    sa.select(Circuit)
                    .where(Circuit.endpoint_id.in_(deployment_ids))
                    .options(
                        selectinload(Circuit.worker_row),
                        selectinload(Circuit.endpoint_row),
                    )
                )
            ).all()
            circuits_by_endpoint: dict[UUID, Circuit] = {
                c.endpoint_id: c for c in circuit_rows if c.endpoint_id is not None
            }

            for item in items:
                results.append(
                    await self._sync_one(sess, item, endpoints_by_id, circuits_by_endpoint)
                )

        return results

    async def update_routes(
        self,
        items: list[UpdateRoutesItem],
    ) -> list[UpdatedRouteSet]:
        """Bulk-replace routing tables for many endpoints in one transaction.

        One SELECT batches every circuit lookup so this path costs O(1)
        DB roundtrips instead of one per endpoint. Per-entry errors
        (no circuit registered yet) are reported in the result without
        aborting the call so a partial set of endpoints can still be
        synced. The service layer reads ``circuit`` / ``old_routes`` to
        fan changes out to workers after commit.
        """
        if not items:
            return []

        deployment_ids = [item.deployment_id for item in items]
        items_by_id: dict[UUID, UpdateRoutesItem] = {item.deployment_id: item for item in items}

        results: list[UpdatedRouteSet] = []

        async with self._begin_session_read_committed() as sess:
            # Lock matching circuit rows for the duration of this
            # transaction so concurrent register / unregister / update
            # callers serialise on the same circuit and cannot lose
            # each other's deltas via read-modify-write on the JSONB
            # ``route_info`` blob. Eager-load worker_row + endpoint_row
            # because the service layer keeps propagating to workers
            # after this transaction closes; touching them lazily would
            # raise DetachedInstanceError.
            circuit_rows = (
                await sess.scalars(
                    sa.select(Circuit)
                    .where(Circuit.endpoint_id.in_(deployment_ids))
                    .options(
                        selectinload(Circuit.worker_row),
                        selectinload(Circuit.endpoint_row),
                    )
                    .with_for_update()
                )
            ).all()
            circuits_by_endpoint: dict[UUID, Circuit] = {
                c.endpoint_id: c for c in circuit_rows if c.endpoint_id is not None
            }

            for deployment_id in deployment_ids:
                circuit = circuits_by_endpoint.get(deployment_id)
                if circuit is None:
                    # Manager pushes routes for any HEALTHY route; the
                    # deployment may not yet have its endpoint registered
                    # if a sync race happens. Mark as failed so the
                    # manager retries on the next short cycle.
                    results.append(
                        UpdatedRouteSet(
                            deployment_id=DeploymentID(deployment_id),
                            success=False,
                            error="No circuit registered for this endpoint yet.",
                            circuit=None,
                            old_routes=[],
                        )
                    )
                    continue

                item = items_by_id[deployment_id]
                new_routes = [
                    RouteInfo(
                        session_id=entry.session_id,
                        session_name=None,
                        route_id=entry.route_id,
                        kernel_host=entry.kernel_host,
                        kernel_port=entry.kernel_port,
                        # Inference circuits are always HTTP; manager does
                        # not push traffic_ratio yet (planned), so the
                        # legacy default keeps every route equal-weighted.
                        protocol=ProxyProtocol.HTTP,
                        traffic_ratio=1.0,
                    )
                    for entry in item.routes
                ]
                old_routes = list(circuit.route_info or [])
                circuit.route_info = new_routes

                results.append(
                    UpdatedRouteSet(
                        deployment_id=DeploymentID(deployment_id),
                        success=True,
                        error=None,
                        circuit=circuit,
                        old_routes=old_routes,
                    )
                )

        return results

    async def register_routes(
        self,
        items: list[RegisterRoutesItem],
    ) -> list[RegisteredRouteSet]:
        """Bulk-append new routes to many circuits in one transaction.

        Delta semantics: each ``circuit.route_info`` is replaced with
        ``existing + new``, where new entries are matched against
        existing ones by ``route_id`` to keep the call idempotent. Per-
        entry errors (no circuit registered yet) are reported in the
        result without aborting the call so a partial set of endpoints
        can still be synced. The service layer reads ``circuit`` /
        ``old_routes`` to fan changes out to workers after commit.
        """
        if not items:
            return []

        deployment_ids = [item.deployment_id for item in items]
        items_by_id: dict[UUID, RegisterRoutesItem] = {item.deployment_id: item for item in items}

        results: list[RegisteredRouteSet] = []

        async with self._begin_session_read_committed() as sess:
            # Lock matching circuit rows for the duration of this
            # transaction so concurrent register / unregister / update
            # callers serialise on the same circuit and cannot lose
            # each other's deltas via read-modify-write on the JSONB
            # ``route_info`` blob. Eager-load worker_row + endpoint_row
            # because the service layer keeps propagating to workers
            # after this transaction closes; touching them lazily would
            # raise DetachedInstanceError.
            circuit_rows = (
                await sess.scalars(
                    sa.select(Circuit)
                    .where(Circuit.endpoint_id.in_(deployment_ids))
                    .options(
                        selectinload(Circuit.worker_row),
                        selectinload(Circuit.endpoint_row),
                    )
                    .with_for_update()
                )
            ).all()
            circuits_by_endpoint: dict[UUID, Circuit] = {
                c.endpoint_id: c for c in circuit_rows if c.endpoint_id is not None
            }

            for deployment_id in deployment_ids:
                circuit = circuits_by_endpoint.get(deployment_id)
                if circuit is None:
                    # Manager may push routes for an endpoint that has
                    # not yet been registered if there is a sync race.
                    # Mark as failed so the manager retries on the next
                    # short cycle.
                    results.append(
                        RegisteredRouteSet(
                            deployment_id=DeploymentID(deployment_id),
                            success=False,
                            error="No circuit registered for this endpoint yet.",
                            circuit=None,
                            old_routes=[],
                            registered_route_ids=[],
                            already_registered_route_ids=[],
                        )
                    )
                    continue

                item = items_by_id[deployment_id]
                existing_routes = list(circuit.route_info or [])
                existing_ids = {route.route_id for route in existing_routes}

                newly_added: list[RouteInfo] = []
                registered_ids: list[UUID] = []
                already_present_ids: list[UUID] = []
                for entry in item.routes:
                    if entry.route_id in existing_ids:
                        already_present_ids.append(entry.route_id)
                        continue
                    newly_added.append(
                        RouteInfo(
                            session_id=entry.session_id,
                            session_name=None,
                            route_id=entry.route_id,
                            kernel_host=entry.kernel_host,
                            kernel_port=entry.kernel_port,
                            # Inference circuits are always HTTP; manager does
                            # not push traffic_ratio yet (planned), so the
                            # legacy default keeps every route equal-weighted.
                            protocol=ProxyProtocol.HTTP,
                            traffic_ratio=1.0,
                        )
                    )
                    registered_ids.append(entry.route_id)

                old_routes = list(existing_routes)
                circuit.route_info = existing_routes + newly_added

                results.append(
                    RegisteredRouteSet(
                        deployment_id=DeploymentID(deployment_id),
                        success=True,
                        error=None,
                        circuit=circuit,
                        old_routes=old_routes,
                        registered_route_ids=registered_ids,
                        already_registered_route_ids=already_present_ids,
                    )
                )

        return results

    async def unregister_routes(
        self,
        items: list[UnregisterRoutesItem],
    ) -> list[UnregisteredRouteSet]:
        """Bulk-drop routes from many circuits in one transaction.

        Delta semantics: each ``circuit.route_info`` is replaced with
        the existing entries minus those whose ``route_id`` is in the
        request set. Already-absent ids are reported as
        ``already_absent_route_ids`` so the call is idempotent. Per-
        entry errors (no circuit registered yet) are reported in the
        result without aborting the call. The service layer reads
        ``circuit`` / ``old_routes`` to fan changes out to workers
        after commit.
        """
        if not items:
            return []

        deployment_ids = [item.deployment_id for item in items]
        items_by_id: dict[UUID, UnregisterRoutesItem] = {item.deployment_id: item for item in items}

        results: list[UnregisteredRouteSet] = []

        async with self._begin_session_read_committed() as sess:
            # Lock matching circuit rows for the duration of this
            # transaction so concurrent register / unregister / update
            # callers serialise on the same circuit and cannot lose
            # each other's deltas via read-modify-write on the JSONB
            # ``route_info`` blob. Eager-load worker_row + endpoint_row
            # because the service layer keeps propagating to workers
            # after this transaction closes; touching them lazily would
            # raise DetachedInstanceError.
            circuit_rows = (
                await sess.scalars(
                    sa.select(Circuit)
                    .where(Circuit.endpoint_id.in_(deployment_ids))
                    .options(
                        selectinload(Circuit.worker_row),
                        selectinload(Circuit.endpoint_row),
                    )
                    .with_for_update()
                )
            ).all()
            circuits_by_endpoint: dict[UUID, Circuit] = {
                c.endpoint_id: c for c in circuit_rows if c.endpoint_id is not None
            }

            for deployment_id in deployment_ids:
                circuit = circuits_by_endpoint.get(deployment_id)
                if circuit is None:
                    results.append(
                        UnregisteredRouteSet(
                            deployment_id=DeploymentID(deployment_id),
                            success=False,
                            error="No circuit registered for this endpoint yet.",
                            circuit=None,
                            old_routes=[],
                            unregistered_route_ids=[],
                            already_absent_route_ids=[],
                        )
                    )
                    continue

                item = items_by_id[deployment_id]
                existing_routes = list(circuit.route_info or [])
                target_ids = set(item.route_ids)

                kept_routes: list[RouteInfo] = []
                dropped_ids: list[UUID] = []
                for route in existing_routes:
                    if route.route_id in target_ids:
                        dropped_ids.append(route.route_id)
                    else:
                        kept_routes.append(route)
                already_absent_ids = [rid for rid in item.route_ids if rid not in dropped_ids]

                old_routes = list(existing_routes)
                circuit.route_info = kept_routes

                results.append(
                    UnregisteredRouteSet(
                        deployment_id=DeploymentID(deployment_id),
                        success=True,
                        error=None,
                        circuit=circuit,
                        old_routes=old_routes,
                        unregistered_route_ids=dropped_ids,
                        already_absent_route_ids=already_absent_ids,
                    )
                )

        return results

    async def delete_endpoints(
        self,
        deployment_ids: list[DeploymentID],
    ) -> list[Circuit]:
        """Bulk-delete endpoints + their circuits in one transaction.

        All DB access uses set-based queries — one SELECT to snapshot the
        rows and their workers, one UPDATE per worker for
        ``occupied_slots`` (grouped by circuit count), and one DELETE
        each for circuits and endpoints. The returned circuits let the
        caller unload them from workers after commit.

        Missing ids are silently skipped — delete is idempotent.
        """
        if not deployment_ids:
            return []

        async with self._begin_session_read_committed() as sess:
            endpoint_rows = (
                await sess.scalars(
                    sa.select(Endpoint)
                    .where(Endpoint.id.in_(deployment_ids))
                    .options(selectinload(Endpoint.circuit_row))
                )
            ).all()
            if not endpoint_rows:
                return []

            circuit_ids: list[UUID] = []
            endpoint_ids_found: list[UUID] = []
            for endpoint in endpoint_rows:
                endpoint_ids_found.append(endpoint.id)
                if endpoint.circuit_row is not None:
                    circuit_ids.append(endpoint.circuit_row.id)

            circuit_rows: list[Circuit] = []
            if circuit_ids:
                circuit_rows = list(
                    (
                        await sess.scalars(
                            sa.select(Circuit)
                            .where(Circuit.id.in_(circuit_ids))
                            .options(selectinload(Circuit.worker_row))
                        )
                    ).all()
                )

            # Aggregate occupied_slots decrements per worker.
            decrement_by_worker: dict[UUID, int] = defaultdict(int)
            for circuit in circuit_rows:
                if circuit.worker_row is not None:
                    decrement_by_worker[circuit.worker_row.id] += 1

            for worker_id, count in decrement_by_worker.items():
                await sess.execute(
                    sa.update(Worker)
                    .where(Worker.id == worker_id)
                    .values(occupied_slots=Worker.occupied_slots - count)
                )

            if circuit_ids:
                await sess.execute(sa.delete(Circuit).where(Circuit.id.in_(circuit_ids)))
            await sess.execute(sa.delete(Endpoint).where(Endpoint.id.in_(endpoint_ids_found)))

        return circuit_rows

    # ---- Private (in-session) helpers ----

    async def _sync_one(
        self,
        sess: SASession,
        item: CreateEndpointItem,
        endpoints_by_id: dict[UUID, Endpoint],
        circuits_by_endpoint: dict[UUID, Circuit],
    ) -> SyncedEndpoint:
        health_check_config = item.health_check
        health_check_enabled = health_check_config is not None

        # Upsert endpoint row using the bulk-fetched snapshot.
        endpoint = endpoints_by_id.get(item.deployment_id)
        if endpoint is not None:
            endpoint.health_check_enabled = health_check_enabled
            endpoint.health_check_config = health_check_config
        else:
            endpoint = Endpoint.create(
                endpoint_id=item.deployment_id,
                health_check_enabled=health_check_enabled,
                health_check_config=health_check_config,
            )
            sess.add(endpoint)
            endpoints_by_id[item.deployment_id] = endpoint

        # Idempotent fast-path: circuit already exists.
        existing = circuits_by_endpoint.get(item.deployment_id)
        if existing is not None:
            existing.endpoint_row = endpoint
            return SyncedEndpoint(
                deployment_id=item.deployment_id,
                url=await existing.get_endpoint_url(),
                health_check_enabled=health_check_enabled,
                new_circuit=None,
            )

        # New circuit — derive worker / port / subdomain from
        # existing_url if provided, else defer to the coordinator's
        # default selection.
        preferred_port: int | None = None
        preferred_subdomain: str | None = None
        worker_id: UUID | None = None
        if item.tags.endpoint.existing_url:
            url = URL(item.tags.endpoint.existing_url)
            (
                worker_id,
                preferred_port,
                preferred_subdomain,
            ) = await self._match_worker_for_existing_url(sess, url)

        # Translate common-DTO tag shapes into coordinator-internal
        # ones expected by ``add_circuit`` (they differ only in field
        # types — UUID vs str — so ``model_dump`` round-trip is the
        # smallest coupling point).
        session_cfg = SessionConfig.model_validate(item.tags.session.model_dump())
        endpoint_cfg = EndpointConfig.model_validate(item.tags.endpoint.model_dump())

        circuit, _worker = await add_circuit(
            sess,
            session_cfg,
            endpoint_cfg,
            item.service_name,
            ProxyProtocol.HTTP,
            AppMode.INFERENCE,
            [],
            open_to_public=item.open_to_public,
            preferred_port=preferred_port,
            preferred_subdomain=preferred_subdomain or item.service_name,
            worker_id=worker_id,
        )
        circuit.endpoint_id = endpoint.id
        circuit.endpoint_row = endpoint
        await sess.flush()
        circuits_by_endpoint[item.deployment_id] = circuit

        return SyncedEndpoint(
            deployment_id=item.deployment_id,
            url=await circuit.get_endpoint_url(),
            health_check_enabled=health_check_enabled,
            new_circuit=circuit,
        )

    async def _match_worker_for_existing_url(
        self,
        sess: SASession,
        existing_url: URL,
    ) -> tuple[UUID | None, int | None, str | None]:
        """Resolve ``existing_url`` to ``(worker_id, preferred_port, preferred_subdomain)``.

        Raises :class:`InvalidURLError` if the URL is unusable.
        """
        if not existing_url.host:
            raise InvalidURLError("URL is missing host component.")
        domain = "." + ".".join(existing_url.host.split(".")[1:])

        query = sa.select(Worker).where(
            Worker.accepted_traffics.contains([AppMode.INFERENCE])
            & (Worker.frontend_mode == FrontendMode.WILDCARD_DOMAIN)
            & (Worker.wildcard_domain == domain)
        )
        result = await sess.execute(query)
        wildcard_match = result.scalar()
        if wildcard_match:
            subdomain = existing_url.host.split(".")[0]
            return wildcard_match.id, None, subdomain

        if not existing_url.port:
            raise InvalidURLError("URL is missing port component for port-based worker.")
        query = sa.select(Worker).where(
            Worker.accepted_traffics.contains([AppMode.INFERENCE])
            & (Worker.frontend_mode == FrontendMode.PORT)
            & (Worker.hostname == existing_url.host)
        )
        result = await sess.execute(query)
        worker_candidates = result.scalars().all()
        matched = [
            w
            for w in worker_candidates
            if w.port_range and w.port_range[0] <= existing_url.port <= w.port_range[1]
        ]
        if matched:
            return matched[0].id, existing_url.port, None
        return None, None, None
