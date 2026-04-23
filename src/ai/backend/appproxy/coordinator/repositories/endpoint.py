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
    SessionConfig,
)
from ai.backend.appproxy.coordinator.errors import InvalidURLError
from ai.backend.appproxy.coordinator.models import Circuit, Endpoint, Worker
from ai.backend.appproxy.coordinator.models.utils import ExtendedAsyncSAEngine
from ai.backend.appproxy.coordinator.models.worker import add_circuit
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import CreateEndpointItem
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
