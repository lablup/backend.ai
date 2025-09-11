from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from yarl import URL

from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.common.exceptions import ObjectNotFound, UnsupportedProtocol
from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
    SerializableCircuit,
)
from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.common.types import ModelServiceStatus, RuntimeVariant

from .base import (
    GUID,
    Base,
    BaseMixin,
    EnumType,
    ForeignKeyIDColumn,
    IDColumn,
    StrEnumType,
    StructuredJSONObjectListColumn,
)

if TYPE_CHECKING:
    pass


__all__ = [
    "Circuit",
]


class Circuit(Base, BaseMixin):
    __tablename__ = "circuits"

    """
    Keep information which will be delivered to proxy-worker when establishing
    port-based TCP and/or websocket proxy server.
    """

    id = IDColumn()

    app = sa.Column(sa.String(length=255), nullable=True)
    protocol = sa.Column(EnumType(ProxyProtocol), nullable=False)

    worker = ForeignKeyIDColumn("worker", "workers.id", nullable=False)

    app_mode = sa.Column(EnumType(AppMode), nullable=False)

    frontend_mode = sa.Column(EnumType(FrontendMode), nullable=False)
    port = sa.Column(sa.Integer(), nullable=True)
    subdomain = sa.Column(sa.String(length=255), nullable=True)

    envs = sa.Column(pgsql.JSONB(), nullable=True)
    arguments = sa.Column(sa.String(length=1000), nullable=True)

    open_to_public = sa.Column(sa.Boolean(), nullable=False, default=False)
    allowed_client_ips = sa.Column(sa.String(length=255), nullable=True)

    user_id = sa.Column(GUID, nullable=True)  # null if `app_mode` is set to `INFERENCE`
    endpoint_id = sa.Column(GUID, nullable=True)
    # null if `app_mode` is set to `INTERACTIVE`
    runtime_variant = sa.Column(
        StrEnumType(RuntimeVariant), nullable=True
    )  # null if `app_mode` is set to `INTERACTIVE`

    session_ids = sa.Column(
        pgsql.ARRAY(GUID),
        nullable=False,
        default=[],
    )
    route_info = sa.Column(StructuredJSONObjectListColumn(RouteInfo), nullable=False, default=[])

    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    worker_row = relationship("Worker", back_populates="circuits")
    endpoint_row = relationship(
        "Endpoint",
        back_populates="circuit_row",
        primaryjoin="Circuit.endpoint_id == Endpoint.id",
        foreign_keys="Circuit.endpoint_id",
        uselist=False,
    )

    # TODO: Create primary key - worker, port, subdomain

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        circuit_id: UUID,
        load_worker=True,
        load_endpoint=True,
    ) -> "Circuit":
        query = sa.select(Circuit).where((Circuit.id == circuit_id))
        if load_worker:
            query = query.options(selectinload(Circuit.worker_row))
        if load_endpoint:
            query = query.options(selectinload(Circuit.endpoint_row))
        circuit = await session.scalar(query)
        if not circuit:
            raise ObjectNotFound(object_name="circuit")
        return circuit

    @classmethod
    async def get_by_endpoint(
        cls,
        session: AsyncSession,
        endpoint_id: UUID,
        load_worker=True,
        load_endpoint=True,
    ) -> "Circuit":
        query = sa.select(Circuit).where((Circuit.endpoint_id == endpoint_id))
        if load_worker:
            query = query.options(selectinload(Circuit.worker_row))
        if load_endpoint:
            query = query.options(selectinload(Circuit.endpoint_row))
        circuit = await session.scalar(query)
        if not circuit:
            raise ObjectNotFound(object_name="circuit")
        return circuit

    @classmethod
    async def list_circuits(
        cls,
        session: AsyncSession,
        load_worker=True,
        load_endpoint=True,
    ) -> Sequence["Circuit"]:
        query = sa.select(Circuit)
        if load_worker:
            query = query.options(selectinload(Circuit.worker_row))
        if load_endpoint:
            query = query.options(selectinload(Circuit.endpoint_row))
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def find(
        cls,
        session: AsyncSession,
        session_id: UUID,
        app: str,
        open_to_public: bool,
        allowed_client_ips: str | None,
    ) -> "Circuit":
        query = (
            sa.select(Circuit)
            .where(
                (Circuit.session_ids.contains([session_id]))
                & (Circuit.app == app)
                & (Circuit.open_to_public == open_to_public)
                & (Circuit.allowed_client_ips == allowed_client_ips)
            )
            .options(selectinload(Circuit.worker_row))
        )
        circuit = await session.scalar(query)
        if not circuit:
            raise ObjectNotFound(object_name="circuit")
        return circuit

    @classmethod
    async def find_by_endpoint(
        cls,
        session: AsyncSession,
        endpoint_id: UUID,
        load_worker=True,
        load_endpoint=True,
    ) -> "Circuit":
        query = sa.select(Circuit).where((Circuit.endpoint_id == endpoint_id))
        if load_worker:
            query = query.options(selectinload(Circuit.worker_row))
        if load_endpoint:
            query = query.options(selectinload(Circuit.endpoint_row))
        circuit = await session.scalar(query)
        if not circuit:
            raise ObjectNotFound(object_name="circuit")
        return circuit

    @classmethod
    def create(
        cls,
        id: UUID,
        app: str,
        protocol: ProxyProtocol,
        worker: UUID,
        app_mode: AppMode,
        frontend_mode: FrontendMode,
        route_info: list[RouteInfo],
        *,
        port: int | None = None,
        subdomain: str | None = None,
        envs: dict[str, Any] | None = None,
        args: str | None = None,
        open_to_public: bool = False,
        allowed_client_ips: str | None = None,
        user_uuid: UUID | None = None,
        endpoint_id: UUID | None = None,
        runtime_variant: RuntimeVariant | None = None,
    ) -> "Circuit":
        c = Circuit()
        c.id = id
        c.app = app
        c.protocol = protocol
        c.worker = worker
        c.app_mode = app_mode
        c.frontend_mode = frontend_mode
        c.port = port
        c.subdomain = subdomain
        c.envs = envs
        c.arguments = args
        c.open_to_public = open_to_public
        c.allowed_client_ips = allowed_client_ips
        c.user_id = user_uuid
        c.endpoint_id = endpoint_id
        c.route_info = route_info
        c.session_ids = [r.session_id for r in route_info]
        c.runtime_variant = runtime_variant

        c.created_at = datetime.now()
        c.updated_at = datetime.now()

        return c

    async def get_endpoint_url(self, session: Optional[AsyncSession] = None) -> URL:
        from .worker import Worker

        worker: Worker = (
            await Worker.get(session, self.worker) if session is not None else self.worker_row
        )

        match (worker.use_tls, self.protocol):
            case (True, ProxyProtocol.TCP):
                scheme = "tls"
            case (False, ProxyProtocol.TCP):
                scheme = "tcp"
            case (_, ProxyProtocol.GRPC):
                scheme = "grpc"
            case (True, ProxyProtocol.HTTP):
                scheme = "https"
            case (False, ProxyProtocol.HTTP):
                scheme = "http"
            case _:
                raise UnsupportedProtocol(self.protocol.name)

        match self.frontend_mode:
            case FrontendMode.WILDCARD_DOMAIN:
                assert self.subdomain and worker.wildcard_domain
                hostname = self.subdomain + worker.wildcard_domain
                if (scheme == "https" and worker.wildcard_traffic_port != 443) or (
                    scheme == "http" and worker.wildcard_traffic_port != 80
                ):
                    hostname += f":{worker.wildcard_traffic_port}"
            case FrontendMode.PORT:
                assert self.port
                hostname = f"{worker.hostname}:{self.port}"

        url = f"{scheme}://{hostname}"
        return URL(url)

    async def get_slot_identity(self) -> str:
        from .worker import Worker

        worker: Worker = self.worker_row
        return f"{worker.authority}:{self.port or self.subdomain}"

    @property
    def traefik_rule(self) -> str:
        match self.protocol:
            case ProxyProtocol.TCP:
                return "ClientIP(`0.0.0.0/0`)"
            case _:
                match self.frontend_mode:
                    case FrontendMode.PORT:
                        return f"Host(`{self.worker_row.hostname}`)"
                    case FrontendMode.WILDCARD_DOMAIN:
                        assert self.subdomain
                        return f"Host(`{self.subdomain}{self.worker_row.wildcard_domain}`)"
                    case _:
                        raise ValueError(
                            f"Invalid frontend mode for traefik setup: {self.frontend_mode}"
                        )

    @property
    def traefik_entrypoint(self) -> str:
        match self.frontend_mode:
            case FrontendMode.WILDCARD_DOMAIN:
                return "domainproxy"
            case FrontendMode.PORT:
                assert self.port
                return f"portproxy_{self.port}"
            case _:
                raise ValueError(f"Invalid frontend mode for traefik setup: {self.frontend_mode}")

    @property
    def traefik_routers(self) -> dict[str, Any]:
        match self.protocol:
            case ProxyProtocol.HTTP:
                base = {
                    "rule": self.traefik_rule,
                    "service": f"bai_service_{self.id}",
                    "entrypoints": [self.traefik_entrypoint],
                    "middlewares": [
                        "CORSHeaders",
                        f"bai_appproxy_plugin_{self.id}",
                        f"bai_appproxy_plugin_{self.id}_go",
                    ],
                }
                if self.worker_row.tls_listen:
                    base["tls"] = ""
                return {f"bai_router_{self.id}": base}
            case ProxyProtocol.TCP:
                return {
                    f"bai_router_{self.id}": {
                        "rule": self.traefik_rule,
                        "service": f"bai_service_{self.id}",
                        "entrypoints": [self.traefik_entrypoint],
                    },
                }
        return {}

    @property
    def healthy_routes(self) -> list[RouteInfo]:
        """
        Get only healthy routes for this circuit.

        Health filtering is only applied for circuits in INFERENCE mode.
        For other modes, all routes are considered healthy.

        Returns:
            List of healthy RouteInfo objects
        """
        # Only apply health filtering for circuits in INFERENCE mode
        if self.app_mode != AppMode.INFERENCE or not self.endpoint_id:
            # No health filtering, return all routes
            return self.route_info

        assert self.endpoint_row
        # Filter routes based on health status stored in JSON
        healthy_routes = []
        for route in self.route_info:
            # Include routes that are explicitly healthy or have no health status (not health-checked)
            if (
                not self.endpoint_row.health_check_enabled
                or route.health_status == ModelServiceStatus.HEALTHY
            ):
                healthy_routes.append(route)

        return healthy_routes

    def update_route_health_status(
        self,
        route_id: UUID,
        health_status: ModelServiceStatus | None,
        last_check_time: float | None = None,
        consecutive_failures: int | None = None,
    ) -> bool:
        """
        Update health status for a specific route in the circuit's route_info

        Args:
            route_id: ID of the route to update
            health_status: New health status
            last_check_time: Timestamp of last health check
            consecutive_failures: Number of consecutive failures

        Returns:
            True if route was found and updated, False otherwise
        """
        for route in self.route_info:
            if route.route_id == route_id:
                did_update_status = False
                if route.health_status != health_status:
                    route.health_status = health_status
                    did_update_status = True
                if last_check_time is not None:
                    route.last_health_check = last_check_time
                if consecutive_failures is not None:
                    route.consecutive_failures = consecutive_failures

                # Mark the route_info column as modified for SQLAlchemy change tracking
                # This is necessary because SQLAlchemy doesn't automatically detect
                # changes to nested objects within JSON columns
                from sqlalchemy.orm import attributes

                attributes.flag_modified(self, "route_info")

                return did_update_status
        return False

    @property
    def traefik_services(self) -> dict[str, Any]:
        # Use health-aware route filtering
        healthy_routes = self.healthy_routes

        # If no healthy routes, return empty config to remove from load balancer
        if not healthy_routes:
            return {}

        base = {  # services should be inserted separately to prevent overwritting whole `services` prefix
            f"bai_service_{self.id}": {
                "weighted": {
                    "services": [
                        {
                            "name": f"bai_session_{r.session_id}_{self.id}",
                            "weight": int(r.traffic_ratio),
                        }
                        for r in healthy_routes
                    ]
                }
            },
        }
        match self.protocol:
            case ProxyProtocol.HTTP:
                for r in healthy_routes:
                    base.update({
                        f"bai_session_{r.session_id}_{self.id}": {
                            "loadBalancer": {
                                "servers": [
                                    {"url": f"http://{r.current_kernel_host}:{r.kernel_port}/"}
                                ],
                            }
                        }
                    })
            case ProxyProtocol.TCP:
                for r in healthy_routes:
                    base.update({
                        f"bai_session_{r.session_id}_{self.id}": {
                            "loadBalancer": {
                                "servers": [
                                    {"address": f"{r.current_kernel_host}:{r.kernel_port}"}
                                ],
                            }
                        }
                    })
        return base

    def get_traefik_middlewares(self, local_config: ServerConfig) -> dict[str, Any]:
        match self.protocol:
            case ProxyProtocol.HTTP:
                traefik_config = local_config.proxy_coordinator.traefik
                assert traefik_config

                return {
                    "CORSHeaders": {
                        "headers": {
                            "accessControlAllowHeaders": "*",
                            "accessControlAllowOriginList": ["*"],
                        },
                    },
                    f"bai_appproxy_plugin_{self.id}": {
                        "plugin": {
                            "appproxy-traefik-plugin": {
                                # Etcd cannot represent bool or None so we're going to just dump the whole JSON
                                "circuit": SerializableCircuit(
                                    **self.dump_model()
                                ).model_dump_json(),
                                "jwt_secret": local_config.secrets.jwt_secret,
                                "permit_hash_secret": local_config.permit_hash.secret.decode(),
                                "permit_cookie_name": PERMIT_COOKIE_NAME,
                            },
                        }
                    },
                    f"bai_appproxy_plugin_{self.id}_go": {
                        "plugin": {
                            "appproxy-traefik-plugin-go": {
                                "id": str(self.id),
                                "sessionids": [str(x) for x in self.session_ids],
                                "lastusedmarkerpath": self.worker_row.traefik_last_used_marker_path,
                            }
                        }
                    },
                }
        return {}
