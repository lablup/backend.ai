import dataclasses
import enum
import json
import textwrap
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Annotated,
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    TypeAlias,
    TypeVar,
    Union,
)
from uuid import UUID

import aiohttp_cors
from aiohttp import web
from pydantic import AliasChoices, AnyUrl, BaseModel, Field

from ai.backend.common.types import ModelServiceStatus, RuntimeVariant

# FIXME: merge majority of common definitions to ai.backend.common when ready


class FrontendMode(enum.StrEnum):
    WILDCARD_DOMAIN = "wildcard"
    PORT = "port"


class FrontendServerMode(enum.StrEnum):
    WILDCARD_DOMAIN = "wildcard"
    PORT = "port"
    TRAEFIK = "traefik"


class ProxyProtocol(enum.StrEnum):
    HTTP = "http"
    GRPC = "grpc"
    HTTP2 = "h2"
    TCP = "tcp"
    PREOPEN = "preopen"


class AppMode(enum.StrEnum):
    INTERACTIVE = "interactive"
    INFERENCE = "inference"


@dataclass
class Slot:
    frontend_mode: FrontendMode
    in_use: bool
    port: int | None
    subdomain: str | None
    circuit_id: UUID | None


class EventLoopType(enum.StrEnum):
    UVLOOP = "uvloop"
    ASYNCIO = "asyncio"


class DigestModType(enum.StrEnum):
    SHA224 = "sha224"
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"


WebRequestHandler: TypeAlias = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
WebMiddleware: TypeAlias = Callable[
    [web.Request, WebRequestHandler],
    Awaitable[web.StreamResponse],
]

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]
AppCreator: TypeAlias = Callable[
    [CORSOptions],
    tuple[web.Application, Iterable[WebMiddleware]],
]


class RouteInfo(BaseModel):
    """
    Information about a route within a circuit.

    Health Status Evaluation:
    Individual route health status is only evaluated and updated when the circuit
    is in INFERENCE mode. For circuits in other modes (e.g., DEVELOPMENT, BATCH),
    health checking is disabled and routes are assumed to be healthy.

    Health status fields (health_status, last_health_check, consecutive_failures)
    are managed by the HealthCheckEngine and stored directly in the circuit's
    route_info JSON column for efficient filtering and atomic updates.
    """

    route_id: Annotated[
        Optional[UUID],
        Field(
            default=None,
            description="Unique identifier for the route. If None, indicates a temporary route.",
            validation_alias=AliasChoices("route-id", "route_id"),
            serialization_alias="route_id",
        ),
    ]
    session_id: Annotated[
        UUID,
        Field(
            ...,
            description="ID of the session associated with this route.",
            validation_alias=AliasChoices("session-id", "session_id"),
            serialization_alias="session_id",
        ),
    ]
    session_name: Annotated[
        Optional[str],
        Field(
            default=None,
            description="Name of the session associated with this route.",
            validation_alias=AliasChoices("session-name", "session_name"),
            serialization_alias="session_name",
        ),
    ]
    kernel_host: Annotated[
        Optional[str],
        Field(
            ...,
            description="Host/IP address of the kernel. This is the address that the proxy will use to connect to the kernel.",
            validation_alias=AliasChoices("kernel-host", "kernel_host"),
            serialization_alias="kernel_host",
        ),
    ]
    kernel_port: Annotated[
        int,
        Field(
            ...,
            description="Port number of the kernel. This is the port that the proxy will use to connect to the kernel.",
            ge=1,
            le=65535,
            validation_alias=AliasChoices("kernel-port", "kernel_port"),
            serialization_alias="kernel_port",
        ),
    ]
    protocol: ProxyProtocol
    traffic_ratio: Annotated[float, Field(default=1.0)]
    health_status: Annotated[
        ModelServiceStatus | None,
        Field(
            default=None,
            description="Health status of this route - only evaluated in INFERENCE mode",
        ),
    ]
    last_health_check: Annotated[
        float | None,
        Field(
            default=None,
            description="Timestamp of last health check - only updated in INFERENCE mode",
        ),
    ]
    consecutive_failures: Annotated[
        int,
        Field(
            default=0,
            description="Number of consecutive health check failures - only tracked in INFERENCE mode",
        ),
    ]

    def __hash__(self) -> int:
        return hash(json.dumps(self.model_dump(mode="json")))

    @property
    def current_kernel_host(self) -> str:
        return self.kernel_host or "localhost"


class SerializableCircuit(BaseModel):
    """
    Serializable representation of `ai.backend.appproxy.coordinator.models.Circuit`
    """

    id: Annotated[UUID, Field(description="ID of circuit.")]

    app: Annotated[
        str,
        Field(
            description="Name of the Backend.AI Kernel app circuit is hosting. Can be a blank string if circuit is referencing an inference app.",
        ),
    ]
    protocol: Annotated[ProxyProtocol, Field(description="Protocol of the Backend.AI Kernel app.")]
    worker: Annotated[UUID, Field(description="ID of the worker hosting the circuit.")]

    app_mode: Annotated[AppMode, Field(description="Application operation mode.")]
    frontend_mode: Annotated[FrontendMode, Field(description="Frontend type of worker.")]

    envs: dict[str, Any]
    arguments: str | None

    open_to_public: Annotated[
        bool,
        Field(
            description=textwrap.dedent(
                """
                Shows if the circuit is open to public.
                For interactive apps, this set as true means users without authorization cookie set will also be able to access application.
                For inference apps it means that API will work without authorization token passed.
                """
            ),
        ),
    ]

    allowed_client_ips: Annotated[
        str | None,
        Field(
            default=None,
            description="Comma separated list of CIDRs accepted as traffic source. null means the circuit is accessible anywhere.",
        ),
    ]

    port: Annotated[
        int | None,
        Field(
            default=None, description="Occupied worker port. Only set if `frontend_mode` is `port`."
        ),
    ]
    subdomain: Annotated[
        str | None,
        Field(
            default=None,
            description="Occupied worker subdomain. Only set if `frontend_mode` is `subdomain`.",
        ),
    ]

    user_id: Annotated[UUID | None, Field(default=None, description="Session owner's UUID.")]
    endpoint_id: Annotated[
        UUID | None,
        Field(
            default=None, description="Model service's UUID. Only set if `app_mode` is inference."
        ),
    ]
    runtime_variant: Annotated[
        str | None,
        Field(
            default=None,
            description="Runtime variant of the model service. Only set if `app_mode` is inference.",
        ),
    ]

    route_info: Annotated[list[RouteInfo], Field(description="List of kernel access information.")]
    session_ids: list[UUID]

    created_at: datetime
    updated_at: datetime

    @property
    def traefik_router_name(self) -> str:
        """ID of the traefik router which represents this circuit."""
        return f"bai_router_{self.id}@etcd"


class SerializableToken(BaseModel):
    login_session_token: str | None
    kernel_host: str
    kernel_port: int
    session_id: UUID
    user_uuid: UUID
    group_id: UUID
    access_key: str
    domain_name: str


class SessionConfig(BaseModel):
    id: Annotated[UUID | None, Field(default=None)]
    user_uuid: UUID
    group_id: UUID
    access_key: Annotated[str | None, Field(default=None)]
    domain_name: str


class EndpointConfig(BaseModel):
    id: UUID
    runtime_variant: Annotated[RuntimeVariant | None, Field(default=None)]
    existing_url: AnyUrl | None


class HealthCheckConfig(BaseModel):
    """
    Health check configuration matching model-definition.yaml schema
    """

    interval: Annotated[float, Field(default=10.0, ge=0)] = 10.0
    path: str
    max_retries: Annotated[int, Field(default=10, ge=1)] = 10
    max_wait_time: Annotated[float, Field(default=15.0, ge=0)] = 15.0
    expected_status_code: Annotated[int, Field(default=200, ge=100, le=599)] = 200


class HealthCheckState(BaseModel):
    """
    Runtime health check state
    """

    current_retry_count: Annotated[int, Field(default=0, ge=0)] = 0
    last_check_time: Annotated[float | None, Field(default=None)] = None
    last_success_time: Annotated[float | None, Field(default=None)] = None
    consecutive_failures: Annotated[int, Field(default=0, ge=0)] = 0
    status: ModelServiceStatus | None = None


class HealthResponse(BaseModel):
    """Standard health check response"""

    status: str
    version: str
    component: str


TBaseModel = TypeVar("TBaseModel", bound=Union[BaseModel, Sequence[BaseModel]])


@dataclass
class PydanticResponse(Generic[TBaseModel]):
    response: TBaseModel
    headers: dict[str, Any] = dataclasses.field(default_factory=lambda: {})
    status: int = 200
