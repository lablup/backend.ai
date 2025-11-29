from datetime import datetime
from typing import TYPE_CHECKING, Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from yarl import URL

from ai.backend.appproxy.common.exceptions import ObjectNotFound, UnsupportedProtocol
from ai.backend.appproxy.common.types import FrontendMode, ProxyProtocol

from .base import GUID, Base, EnumType, IDColumn

if TYPE_CHECKING:
    from .worker import Worker


__all__ = [
    "StaticAddress",
]


class StaticAddress(Base):
    __tablename__ = "static_addresses"

    """
    Represents a static network address that can be allocated to circuits.
    This allows separating the lifecycle of network addresses from the circuits that use them,
    similar to AWS Elastic IP or Google Cloud Static External IP.
    """

    id = IDColumn()

    # Network address configuration
    frontend_mode = sa.Column(EnumType(FrontendMode), nullable=False)
    port = sa.Column(sa.Integer(), nullable=True)
    subdomain = sa.Column(sa.String(length=255), nullable=True)

    # Allocation status
    is_allocated = sa.Column(sa.Boolean(), nullable=False, default=False)
    allocated_to_circuit = sa.Column(GUID, nullable=True)

    # Metadata
    name = sa.Column(sa.String(length=255), nullable=True)
    description = sa.Column(sa.String(length=1000), nullable=True)
    auto_created = sa.Column(sa.Boolean(), nullable=False, default=False)

    # Constraints - ensure only one address type is specified
    __table_args__ = (
        sa.CheckConstraint(
            "(frontend_mode = 'port' AND port IS NOT NULL AND subdomain IS NULL) OR "
            "(frontend_mode = 'wildcard' AND subdomain IS NOT NULL AND port IS NULL)",
            name="ck_static_addresses_frontend_mode_constraint",
        ),
        sa.Index("ix_static_addresses_allocated_circuit", "allocated_to_circuit"),
        sa.Index("ix_static_addresses_port", "port"),
        sa.Index("ix_static_addresses_subdomain", "subdomain"),
    )

    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Relationship to circuits (one-to-one when allocated)
    circuit = relationship(
        "Circuit", back_populates="static_address", foreign_keys="Circuit.static_address_id"
    )

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        static_address_id: UUID,
        load_circuit: bool = False,
    ) -> "StaticAddress":
        query = sa.select(StaticAddress).where(StaticAddress.id == static_address_id)
        if load_circuit:
            query = query.options(selectinload(StaticAddress.circuit))
        static_address = await session.scalar(query)
        if not static_address:
            raise ObjectNotFound(object_name="static_address")
        return static_address

    @classmethod
    async def list_static_addresses(
        cls,
        session: AsyncSession,
        load_circuit: bool = False,
        allocated_only: bool = False,
        available_only: bool = False,
    ) -> Sequence["StaticAddress"]:
        query = sa.select(StaticAddress)

        if allocated_only:
            query = query.where(StaticAddress.is_allocated)
        elif available_only:
            query = query.where(~StaticAddress.is_allocated)

        if load_circuit:
            query = query.options(selectinload(StaticAddress.circuit))

        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def find_by_address(
        cls,
        session: AsyncSession,
        frontend_mode: FrontendMode,
        port: int | None = None,
        subdomain: str | None = None,
    ) -> "StaticAddress":
        """Find a static address by its network address components"""
        if frontend_mode == FrontendMode.PORT:
            if port is None:
                raise ValueError("Port must be specified for PORT frontend mode")
            query = sa.select(StaticAddress).where(
                (StaticAddress.frontend_mode == frontend_mode) & (StaticAddress.port == port)
            )
        else:  # FrontendMode.WILDCARD_DOMAIN
            if subdomain is None:
                raise ValueError("Subdomain must be specified for WILDCARD_DOMAIN frontend mode")
            query = sa.select(StaticAddress).where(
                (StaticAddress.frontend_mode == frontend_mode)
                & (StaticAddress.subdomain == subdomain)
            )

        static_address = await session.scalar(query)
        if not static_address:
            raise ObjectNotFound(object_name="static_address")
        return static_address

    @classmethod
    async def find_available_address(
        cls,
        session: AsyncSession,
        frontend_mode: FrontendMode,
        preferred_port: int | None = None,
        preferred_subdomain: str | None = None,
    ) -> "StaticAddress | None":
        """Find an available static address matching the criteria"""
        query = sa.select(StaticAddress).where(
            (StaticAddress.frontend_mode == frontend_mode) & (~StaticAddress.is_allocated)
        )

        if frontend_mode == FrontendMode.PORT and preferred_port:
            query = query.where(StaticAddress.port == preferred_port)
        elif frontend_mode == FrontendMode.WILDCARD_DOMAIN and preferred_subdomain:
            query = query.where(StaticAddress.subdomain == preferred_subdomain)

        return await session.scalar(query)

    @classmethod
    def create(
        cls,
        frontend_mode: FrontendMode,
        *,
        port: int | None = None,
        subdomain: str | None = None,
        name: str | None = None,
        description: str | None = None,
        auto_created: bool = False,
    ) -> "StaticAddress":
        """Create a new static address"""
        # Validate input
        if frontend_mode == FrontendMode.PORT:
            if port is None:
                raise ValueError("Port must be specified for PORT frontend mode")
            if subdomain is not None:
                raise ValueError("Subdomain must not be specified for PORT frontend mode")
        else:  # FrontendMode.WILDCARD_DOMAIN
            if subdomain is None:
                raise ValueError("Subdomain must be specified for WILDCARD_DOMAIN frontend mode")
            if port is not None:
                raise ValueError("Port must not be specified for WILDCARD_DOMAIN frontend mode")

        addr = cls()
        addr.frontend_mode = frontend_mode
        addr.port = port
        addr.subdomain = subdomain
        addr.name = name
        addr.description = description
        addr.auto_created = auto_created
        addr.is_allocated = False
        addr.allocated_to_circuit = None
        addr.created_at = datetime.now()
        addr.updated_at = datetime.now()

        return addr

    async def allocate_to_circuit(self, circuit_id: UUID) -> None:
        """Allocate this static address to a circuit"""
        if self.is_allocated:
            raise ValueError(
                f"Static address {self.id} is already allocated to circuit {self.allocated_to_circuit}"
            )

        self.is_allocated = True
        self.allocated_to_circuit = circuit_id
        self.updated_at = datetime.now()

    async def deallocate(self) -> None:
        """Deallocate this static address from its current circuit"""
        self.is_allocated = False
        self.allocated_to_circuit = None
        self.updated_at = datetime.now()

    async def get_endpoint_url(self, worker: "Worker", protocol: ProxyProtocol) -> URL:
        """Generate the endpoint URL for this static address using the given worker and protocol"""
        match (worker.use_tls, protocol):
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
                raise UnsupportedProtocol(protocol.name)

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

    @property
    def address_display(self) -> str:
        """Human-readable representation of the address"""
        if self.frontend_mode == FrontendMode.PORT:
            return f"port:{self.port}"
        else:
            return f"subdomain:{self.subdomain}"
