import logging
import uuid
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    pass

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from yarl import URL

from ai.backend.appproxy.common.exceptions import (
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
from ai.backend.logging import BraceStyleAdapter

from .base import Base, BaseMixin, EnumType, ForeignKeyIDColumn, IDColumn, StrEnumType
from .circuit import Circuit

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = [
    "Worker",
    "WorkerAppFilter",
    "WorkerStatus",
    "pick_worker",
    "add_circuit",
]


class WorkerStatus(StrEnum):
    ALIVE = "ALIVE"
    LOST = "LOST"
    TERMINATED = "TERMINATED"


class Worker(Base, BaseMixin):
    __tablename__ = "workers"

    id = IDColumn()

    authority = sa.Column(
        sa.String(length=255), nullable=False, unique=True
    )  # Human-readable identity of each AppProxy worker, must be identical across all AppProxy workers under single VIP when HA is set up
    frontend_mode = sa.Column(
        EnumType(FrontendMode), nullable=False
    )  # will be fixed as `port` when `protocol` is set to `tcp`
    protocol = sa.Column(EnumType(ProxyProtocol), nullable=False)  # type of traffic to procy

    hostname = sa.Column(
        sa.String(length=1024), nullable=False
    )  # Hostname which users utilize to access this AppProxy
    tls_listen = sa.Column(
        sa.Boolean(), default=False
    )  # Indicates if TLS is required to access the AppProxy
    tls_advertised = sa.Column(
        sa.Boolean(), default=False
    )  # Indicates if TLS is required to access the AppProxy

    api_port = sa.Column(sa.Integer(), nullable=False)  # REST API port

    available_slots = sa.Column(
        sa.Integer(), default=0, nullable=False
    )  # set to -1 when `frontend_mode` is set to `wildcard`
    occupied_slots = sa.Column(sa.Integer(), default=0, nullable=False)

    # Only set if `frontend_mode` is `port`
    port_range = sa.Column(pgsql.ARRAY(sa.Integer), nullable=True)

    # Only set if `frontend_mode` is `wildcard`
    # .example.com
    wildcard_domain = sa.Column(sa.String(length=1024), nullable=True)
    # Only set if `frontend_mode` is `wildcard`
    wildcard_traffic_port = sa.Column(sa.Integer(), nullable=True)

    nodes = sa.Column(sa.Integer(), default=1, nullable=False)

    accepted_traffics = sa.Column(pgsql.ARRAY(EnumType(AppMode)), nullable=False)
    filtered_apps_only = sa.Column(sa.Boolean(), default=False, nullable=False)

    traefik_last_used_marker_path = sa.Column(sa.String(length=1024), nullable=True)

    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    status = sa.Column(
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
        load_filters=False,
        load_circuits=False,
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
        load_filters=False,
        load_circuits=False,
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
        load_filters=False,
        load_circuits=False,
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
        filtered_apps_only=False,
        status=WorkerStatus.LOST,
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
        match frontend_mode:
            case FrontendMode.WILDCARD_DOMAIN:
                assert wildcard_domain
                w.available_slots = -1
            case FrontendMode.PORT:
                assert port_range
                w.available_slots = port_range[1] - port_range[0] + 1

        return w

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
        circuits: list[Circuit] = (await session.execute(circuit_list_query)).scalars().all()
        match self.frontend_mode:
            case FrontendMode.PORT:
                assert self.port_range
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


class WorkerAppFilter(Base, BaseMixin):
    __tablename__ = "worker_app_filters"

    id = IDColumn()

    property_name = sa.Column(sa.VARCHAR(96), nullable=False)
    property_value = sa.Column(sa.VARCHAR(1024), nullable=False)
    worker = ForeignKeyIDColumn("worker", "workers.id", nullable=False)

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


async def add_circuit(
    session: AsyncSession,
    session_info: SessionConfig,
    endpoint_info: EndpointConfig | None,
    app: str,
    protocol: ProxyProtocol,
    mode: AppMode,
    routes: list[RouteInfo],
    *,
    envs: dict[str, Any] = {},
    args: str | None = None,
    open_to_public=False,
    allowed_client_ips: str | None = None,
    preferred_port: int | None = None,
    preferred_subdomain: str | None = None,
    worker_id: UUID | None = None,
) -> tuple[Circuit, Worker]:
    if worker_id:
        worker = await Worker.get(session, worker_id, load_circuits=True)
        if worker.available_slots - worker.occupied_slots <= 0 and worker.available_slots >= 0:
            raise WorkerNotAvailable
    else:
        worker = await pick_worker(session, session_info, endpoint_info, protocol, mode)

    circuit_params: dict[str, Any] = {}

    if worker.frontend_mode == FrontendMode.WILDCARD_DOMAIN:
        acquired_subdomains = [c.subdomain for c in worker.circuits]
        if _requested_subdomain := preferred_subdomain:
            subdomain = _requested_subdomain
        else:
            sub_id = str(uuid.uuid4()).split("-")[0]
            subdomain = f"app-{sub_id}"

        while subdomain in acquired_subdomains:
            sub_id = str(uuid.uuid4()).split("-")[0]
            subdomain = f"{_requested_subdomain}-{sub_id}"
        circuit_params["subdomain"] = subdomain
    else:
        acquired_ports = set([c.port for c in worker.circuits])
        port_range = worker.port_range
        assert port_range
        port_pool = set(range(port_range[0], port_range[1] + 1)) - acquired_ports
        if _requested_port := preferred_port:
            if _requested_port not in port_pool:
                raise PortNotAvailable
            port = _requested_port
        else:
            if len(port_pool) == 0:
                raise PortNotAvailable
            port = port_pool.pop()
        circuit_params["port"] = port

    circuit = Circuit.create(
        uuid.uuid4(),
        app,
        protocol,
        worker.id,
        mode,
        worker.frontend_mode,
        routes,
        envs=envs,
        args=args,
        open_to_public=open_to_public,
        allowed_client_ips=allowed_client_ips,
        user_uuid=session_info.user_uuid,
        endpoint_id=endpoint_info.id if endpoint_info else None,
        runtime_variant=endpoint_info.runtime_variant if endpoint_info else None,
        **circuit_params,
    )
    circuit.worker_row = worker

    worker.occupied_slots += 1
    session.add(circuit)
    return (circuit, worker)
