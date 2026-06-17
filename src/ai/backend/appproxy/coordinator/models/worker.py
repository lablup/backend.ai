import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    pass

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from yarl import URL

from ai.backend.appproxy.common.errors import (
    ObjectNotFound,
    PortNotAvailable,
    WorkerNotAvailable,
)
from ai.backend.appproxy.common.types import (
    AppMode,
    EndpointConfig,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
    SessionConfig,
    Slot,
)
from ai.backend.appproxy.coordinator.errors import (
    MissingFrontendConfigError,
    SubdomainAllocationError,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import Subdomain
from ai.backend.logging import BraceStyleAdapter

from .base import GUID, Base, BaseMixin, EnumType, StrEnumType
from .circuit import Circuit
from .subdomain import SubdomainGenerator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = [
    "Worker",
    "WorkerAppFilter",
    "WorkerStatus",
    "add_circuit",
    "pick_worker",
]


class WorkerStatus(StrEnum):
    ALIVE = "ALIVE"
    LOST = "LOST"
    TERMINATED = "TERMINATED"


class Worker(Base, BaseMixin):  # type: ignore[misc]
    __tablename__ = "workers"

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    authority: Mapped[str] = mapped_column(
        sa.String(length=255), nullable=False, unique=True
    )  # Human-readable identity of each AppProxy worker, must be identical across all AppProxy workers under single VIP when HA is set up
    frontend_mode: Mapped[FrontendMode] = mapped_column(
        EnumType(FrontendMode), nullable=False
    )  # will be fixed as `port` when `protocol` is set to `tcp`
    protocol: Mapped[ProxyProtocol] = mapped_column(
        EnumType(ProxyProtocol), nullable=False
    )  # type of traffic to procy

    hostname: Mapped[str] = mapped_column(
        sa.String(length=1024), nullable=False
    )  # Hostname which users utilize to access this AppProxy
    tls_listen: Mapped[bool] = mapped_column(
        sa.Boolean(), default=False, nullable=False
    )  # Indicates if TLS is required to access the AppProxy
    tls_advertised: Mapped[bool] = mapped_column(
        sa.Boolean(), default=False, nullable=False
    )  # Indicates if TLS is required to access the AppProxy

    api_port: Mapped[int] = mapped_column(sa.Integer(), nullable=False)  # REST API port

    available_slots: Mapped[int] = mapped_column(
        sa.Integer(), default=0, nullable=False
    )  # set to -1 when `frontend_mode` is set to `wildcard`
    occupied_slots: Mapped[int] = mapped_column(sa.Integer(), default=0, nullable=False)

    # Only set if `frontend_mode` is `port`
    port_range: Mapped[tuple[int, int] | None] = mapped_column(
        pgsql.ARRAY(sa.Integer), nullable=True
    )

    # Only set if `frontend_mode` is `wildcard`
    # .example.com
    wildcard_domain: Mapped[str | None] = mapped_column(sa.String(length=1024), nullable=True)
    # Only set if `frontend_mode` is `wildcard`
    wildcard_traffic_port: Mapped[int | None] = mapped_column(sa.Integer(), nullable=True)

    nodes: Mapped[int] = mapped_column(sa.Integer(), default=1, nullable=False)

    accepted_traffics: Mapped[list[AppMode]] = mapped_column(
        pgsql.ARRAY(EnumType(AppMode)), nullable=False
    )
    filtered_apps_only: Mapped[bool] = mapped_column(sa.Boolean(), default=False, nullable=False)

    traefik_last_used_marker_path: Mapped[str | None] = mapped_column(
        sa.String(length=1024), nullable=True
    )

    created_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )

    status: Mapped[WorkerStatus] = mapped_column(
        StrEnumType(WorkerStatus),
        default=WorkerStatus.ALIVE,
        nullable=False,
    )

    filters = relationship(
        "WorkerAppFilter",
        back_populates="worker_row",
    )
    circuits = relationship(
        "Circuit",
        back_populates="worker_row",
    )

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        worker_id: UUID,
        load_filters: bool = False,
        load_circuits: bool = False,
    ) -> "Worker":
        query = sa.select(Worker).filter(Worker.id == worker_id)
        if load_filters:
            query = query.options(selectinload(Worker.filters))
        if load_circuits:
            query = query.options(selectinload(Worker.circuits))
        worker = await session.scalar(query)
        if not worker:
            raise ObjectNotFound(object_name="worker")
        return worker

    @classmethod
    async def find_by_authority(
        cls,
        session: AsyncSession,
        authority: str,
        load_filters: bool = False,
        load_circuits: bool = False,
    ) -> "Worker":
        query = sa.select(Worker).filter(Worker.authority == authority)
        if load_filters:
            query = query.options(selectinload(Worker.filters))
        if load_circuits:
            query = query.options(selectinload(Worker.circuits))
        worker = await session.scalar(query)
        if not worker:
            raise ObjectNotFound(object_name="worker")
        return worker

    @classmethod
    async def list_workers(
        cls,
        session: AsyncSession,
        load_filters: bool = False,
        load_circuits: bool = False,
    ) -> list["Worker"]:
        query = sa.select(Worker)
        if load_filters:
            query = query.options(selectinload(Worker.filters))
        if load_circuits:
            query = query.options(selectinload(Worker.circuits))
        worker = await session.scalars(query)
        return list(worker)

    @classmethod
    def create(
        cls,
        id: UUID,
        authority: str,
        frontend_mode: FrontendMode,
        protocol: ProxyProtocol,
        hostname: str,
        tls_listen: bool,
        tls_advertised: bool,
        api_port: int,
        accepted_traffics: list[AppMode],
        *,
        port_range: tuple[int, int] | None = None,
        wildcard_domain: str | None = None,
        wildcard_traffic_port: int | None = None,
        traefik_last_used_marker_path: str | None = None,
        filtered_apps_only: bool = False,
        status: WorkerStatus = WorkerStatus.LOST,
    ) -> "Worker":
        w = cls()
        w.id = id
        w.authority = authority
        w.frontend_mode = frontend_mode
        w.protocol = protocol
        w.hostname = hostname
        w.tls_listen = tls_listen
        w.tls_advertised = tls_advertised
        w.api_port = api_port
        w.accepted_traffics = accepted_traffics
        w.port_range = port_range
        w.wildcard_domain = wildcard_domain
        w.wildcard_traffic_port = wildcard_traffic_port
        w.filtered_apps_only = filtered_apps_only
        w.traefik_last_used_marker_path = traefik_last_used_marker_path
        w.status = status

        w.occupied_slots = 0
        w.refresh_available_slots()

        return w

    def _calculate_available_slots(self) -> int:
        """Number of available slots derived from the current frontend configuration."""
        match self.frontend_mode:
            case FrontendMode.WILDCARD_DOMAIN:
                if not self.wildcard_domain:
                    raise MissingFrontendConfigError(
                        "Wildcard domain is required for WILDCARD_DOMAIN frontend mode"
                    )
                return -1
            case FrontendMode.PORT:
                if not self.port_range:
                    raise MissingFrontendConfigError(
                        "Port range is required for PORT frontend mode"
                    )
                return self.port_range[1] - self.port_range[0] + 1
        raise UnreachableError(f"Unsupported frontend mode: {self.frontend_mode}")

    def refresh_available_slots(self) -> None:
        """Recompute available_slots from the current frontend config."""
        self.available_slots = self._calculate_available_slots()

    @property
    def use_tls(self) -> bool:
        return self.tls_listen or self.tls_advertised

    @property
    def api_endpoint(self) -> URL:
        should_include_port = (not self.use_tls and self.api_port != 80) or (
            self.use_tls and self.api_port != 443
        )
        base_url = f"{'https' if self.use_tls else 'http'}://{self.hostname}"
        if should_include_port:
            base_url += f":{self.api_port}"
        return URL(base_url)

    async def list_slots(self, session: AsyncSession) -> list[Slot]:
        """
        For workers working with PORT-based frontend_mode, this will list all available and occupied slots
        For workers with SUBDOMAIN, this will list occupied slots only - we can't list all available slots since it is infinite
        """
        circuit_list_query = sa.select(Circuit).where(Circuit.worker == self.id)
        circuits: Sequence[Circuit] = (await session.execute(circuit_list_query)).scalars().all()
        match self.frontend_mode:
            case FrontendMode.PORT:
                if not self.port_range:
                    raise MissingFrontendConfigError(
                        "Port range is required for PORT frontend mode"
                    )
                occupied_ports: dict[int, UUID] = {c.port: c.id for c in circuits if c.port}
                slots = [
                    Slot(
                        FrontendMode.PORT,
                        port in occupied_ports,
                        port=port,
                        subdomain=None,
                        circuit_id=occupied_ports.get(port),
                    )
                    for port in range(self.port_range[0], self.port_range[1] + 1)
                ]
            case FrontendMode.WILDCARD_DOMAIN:
                slots = [
                    Slot(
                        FrontendMode.WILDCARD_DOMAIN,
                        True,
                        port=None,
                        subdomain=c.subdomain,
                        circuit_id=c.id,
                    )
                    for c in circuits
                ]
            case _:
                raise ValueError(f"Invalid frontend mode: {self.frontend_mode}")
        return slots


class WorkerAppFilter(Base, BaseMixin):  # type: ignore[misc]
    __tablename__ = "worker_app_filters"

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    property_name: Mapped[str] = mapped_column(sa.VARCHAR(96), nullable=False)
    property_value: Mapped[str] = mapped_column(sa.VARCHAR(1024), nullable=False)
    worker: Mapped[UUID] = mapped_column(GUID, sa.ForeignKey("workers.id"), nullable=False)

    worker_row = relationship("Worker", back_populates="filters")

    __table_args__ = (
        sa.UniqueConstraint(
            "worker",
            "property_name",
            "property_value",
            name="uq_worker_app_filter_worker_property_name_property_value",
        ),
    )

    @classmethod
    def create(
        cls, id: UUID, property_name: str, property_value: str, worker: UUID
    ) -> "WorkerAppFilter":
        filter = WorkerAppFilter()
        filter.id = id
        filter.property_name = property_name
        filter.property_value = property_value
        filter.worker = worker
        return filter

    @classmethod
    async def find_by_rule(
        cls, session: AsyncSession, worker: UUID, name: str, value: str
    ) -> "WorkerAppFilter":
        query = sa.select(WorkerAppFilter).where(
            (WorkerAppFilter.worker == worker)
            & (WorkerAppFilter.property_name == name)
            & (WorkerAppFilter.property_value == value)
        )
        rule = await session.scalar(query)
        if not rule:
            raise ObjectNotFound(object_name="worker_app_filter")
        return rule


async def pick_worker(
    session: AsyncSession,
    session_info: SessionConfig,
    endpoint_info: EndpointConfig | None,
    protocol: ProxyProtocol,
    app_mode: AppMode,
) -> Worker:
    app_filter_queries = [
        (WorkerAppFilter.property_name == f"session.{key}")
        & (WorkerAppFilter.property_value == str(value))
        for key, value in session_info.model_dump().items()
    ]
    if endpoint_info:
        app_filter_queries += [
            (WorkerAppFilter.property_name == f"endpoint.{key}")
            & (WorkerAppFilter.property_value == str(value))
            for key, value in endpoint_info.model_dump().items()
        ]
    where_clause = app_filter_queries[0]
    for q in app_filter_queries[1:]:
        where_clause |= q
    query = sa.select(WorkerAppFilter).where(where_clause)
    filter_result = await session.execute(query)
    worker_ids = [app_filter.worker for app_filter in filter_result.scalars().all()]

    log.debug("protocol: {} ({})", protocol, type(protocol))
    worker_query = sa.select(Worker).where(
        (Worker.protocol == protocol)
        & (Worker.accepted_traffics.contains([app_mode]))
        & (Worker.status == WorkerStatus.ALIVE)
    )
    if worker_ids:
        worker_query = worker_query.where(
            Worker.filtered_apps_only & (Worker.accepted_traffics.contains(app_mode))
        )
    result = await session.execute(worker_query)
    sorted_workers: list[Worker] = [
        f
        for f in sorted(
            result.scalars().all(),
            key=lambda f: (
                -1
                if f.frontend_mode == FrontendMode.WILDCARD_DOMAIN
                else (f.available_slots - f.occupied_slots) * -1
            ),
            reverse=True,
        )
        if f.frontend_mode == FrontendMode.WILDCARD_DOMAIN
        or (f.available_slots - f.occupied_slots) > 0
    ]
    if not sorted_workers:
        raise WorkerNotAvailable
    worker = sorted_workers[0]
    return await Worker.get(
        session,
        worker.id,
        load_circuits=True,
    )


# Bounded retries for the rare race where two concurrent requests pick the same
# normalized subdomain: the DB unique index rejects the duplicate and we retry
# with a fresh suffix.
_MAX_SUBDOMAIN_ATTEMPTS = 10


def _is_subdomain_unique_violation(error: IntegrityError) -> bool:
    """True if ``error`` is the circuits subdomain unique-index violation (23505)."""
    return getattr(error.orig, "pgcode", None) == "23505" and "uq_circuits_worker_subdomain" in str(
        error.orig
    )


@dataclass(frozen=True)
class WildcardCircuitInput:
    """Inputs for creating a single wildcard-domain-mode circuit."""

    session: AsyncSession
    worker: Worker
    app: str
    protocol: ProxyProtocol
    mode: AppMode
    routes: list[RouteInfo]
    session_info: SessionConfig
    endpoint_info: EndpointConfig | None
    preferred_subdomain: str | None
    envs: dict[str, Any]
    args: str | None
    open_to_public: bool
    allowed_client_ips: str | None


@dataclass(frozen=True)
class PortCircuitInput:
    """Inputs for creating a single port-mode circuit."""

    session: AsyncSession
    worker: Worker
    app: str
    protocol: ProxyProtocol
    mode: AppMode
    routes: list[RouteInfo]
    session_info: SessionConfig
    endpoint_info: EndpointConfig | None
    preferred_port: int | None
    envs: dict[str, Any]
    args: str | None
    open_to_public: bool
    allowed_client_ips: str | None


async def add_circuit(
    session: AsyncSession,
    session_info: SessionConfig,
    endpoint_info: EndpointConfig | None,
    app: str,
    protocol: ProxyProtocol,
    mode: AppMode,
    routes: list[RouteInfo],
    *,
    envs: dict[str, Any] | None = None,
    args: str | None = None,
    open_to_public: bool = False,
    allowed_client_ips: str | None = None,
    preferred_port: int | None = None,
    preferred_subdomain: str | None = None,
    worker_id: UUID | None = None,
) -> tuple[Circuit, Worker]:
    if envs is None:
        envs = {}
    if worker_id:
        worker = await Worker.get(session, worker_id, load_circuits=True)
        if worker.available_slots - worker.occupied_slots <= 0 and worker.available_slots >= 0:
            raise WorkerNotAvailable
    else:
        worker = await pick_worker(session, session_info, endpoint_info, protocol, mode)

    if worker.frontend_mode == FrontendMode.WILDCARD_DOMAIN:
        generator = SubdomainGenerator()
        preferred = Subdomain(preferred_subdomain) if preferred_subdomain else None
        # Subdomains already taken on this worker; the generator avoids
        # collisions against them while normalizing the requested name.
        taken: set[Subdomain] = {Subdomain(c.subdomain) for c in worker.circuits if c.subdomain}
        circuit_params["subdomain"] = generator.generate_subdomain(preferred, taken)
    else:
        circuit = await _allocate_port_circuit(
            PortCircuitInput(
                session=session,
                worker=worker,
                app=app,
                protocol=protocol,
                mode=mode,
                routes=routes,
                session_info=session_info,
                endpoint_info=endpoint_info,
                preferred_port=preferred_port,
                envs=envs,
                args=args,
                open_to_public=open_to_public,
                allowed_client_ips=allowed_client_ips,
            )
        )

    worker.occupied_slots += 1
    return (circuit, worker)


async def _allocate_port_circuit(spec: PortCircuitInput) -> Circuit:
    """Allocate a free port on the worker and create a port-mode circuit."""
    worker = spec.worker
    acquired_ports = {c.port for c in worker.circuits}
    port_range = worker.port_range
    if not port_range:
        raise MissingFrontendConfigError("Port range is required for PORT frontend mode")
    port_pool = set(range(port_range[0], port_range[1] + 1)) - acquired_ports
    if _requested_port := spec.preferred_port:
        if _requested_port not in port_pool:
            raise PortNotAvailable
        port = _requested_port
    else:
        if len(port_pool) == 0:
            raise PortNotAvailable
        port = port_pool.pop()
    circuit = Circuit.create_port_mode(
        uuid.uuid4(),
        spec.app,
        spec.protocol,
        worker.id,
        spec.mode,
        spec.routes,
        port,
        envs=spec.envs,
        args=spec.args,
        open_to_public=spec.open_to_public,
        allowed_client_ips=spec.allowed_client_ips,
        user_uuid=spec.session_info.user_uuid,
        endpoint_id=spec.endpoint_info.id if spec.endpoint_info else None,
        runtime_variant=spec.endpoint_info.runtime_variant if spec.endpoint_info else None,
    )
    circuit.worker_row = worker
    spec.session.add(circuit)
    return circuit


async def _allocate_wildcard_circuit(spec: WildcardCircuitInput) -> Circuit:
    """Create a wildcard-domain circuit, normalizing the requested subdomain and
    retrying with a fresh suffix when the per-worker unique index rejects it.

    The flush runs inside a savepoint so a unique-violation rolls back only the
    failed insert, leaving the enclosing transaction usable for the retry.
    """
    session = spec.session
    generator = SubdomainGenerator()
    subdomain = Subdomain(spec.preferred_subdomain) if spec.preferred_subdomain else None
    taken: set[Subdomain] = {Subdomain(c.subdomain) for c in spec.worker.circuits if c.subdomain}
    last_error: IntegrityError | None = None
    for _ in range(_MAX_SUBDOMAIN_ATTEMPTS):
        subdomain = generator.generate_subdomain(subdomain, taken)
        taken.add(subdomain)
        circuit = Circuit.create_domain_mode(
            uuid.uuid4(),
            spec.app,
            spec.protocol,
            spec.worker.id,
            spec.mode,
            spec.routes,
            subdomain,
            envs=spec.envs,
            args=spec.args,
            open_to_public=spec.open_to_public,
            allowed_client_ips=spec.allowed_client_ips,
            user_uuid=spec.session_info.user_uuid,
            endpoint_id=spec.endpoint_info.id if spec.endpoint_info else None,
            runtime_variant=spec.endpoint_info.runtime_variant if spec.endpoint_info else None,
        )
        circuit.worker_row = spec.worker
        session.add(circuit)
        try:
            async with session.begin_nested():
                await session.flush()
        except IntegrityError as e:
            if not _is_subdomain_unique_violation(e):
                raise
            session.expunge(circuit)
            last_error = e
            continue
        return circuit
    raise SubdomainAllocationError(
        f"Could not allocate a unique subdomain on worker {spec.worker.id} "
        f"after {_MAX_SUBDOMAIN_ATTEMPTS} attempts."
    ) from last_error
