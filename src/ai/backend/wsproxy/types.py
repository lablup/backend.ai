import dataclasses
import enum
import textwrap
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Annotated,
    Any,
    Awaitable,
    Callable,
    Final,
    Generic,
    Iterable,
    Mapping,
    TypeAlias,
    TypeVar,
)
from uuid import UUID

import aiohttp_cors
from aiohttp import web
from pydantic import AnyUrl, BaseModel, Field

# FIXME: merge majority of common definitions to ai.backend.common when ready


class FrontendMode(str, enum.Enum):
    PORT = "port"


class ProxyProtocol(str, enum.Enum):
    HTTP = "http"
    GRPC = "grpc"
    HTTP2 = "h2"
    TCP = "tcp"
    PREOPEN = "preopen"


class AppMode(str, enum.Enum):
    INTERACTIVE = "interactive"
    INFERENCE = "inference"


@dataclass
class Slot:
    frontend_mode: FrontendMode
    in_use: bool
    port: int | None
    circuit_id: UUID | None


class EventLoopType(str, enum.Enum):
    UVLOOP = "uvloop"
    ASYNCIO = "asyncio"


class DigestModType(str, enum.Enum):
    SHA1 = "sha1"
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
    session_id: UUID
    session_name: Annotated[str | None, Field(default=None)]
    kernel_host: str
    kernel_port: int
    protocol: ProxyProtocol
    traffic_ratio: Annotated[float, Field(default=1.0)]


@dataclass
class PortFrontendInfo:
    port: int


@dataclass
class InteractiveAppInfo:
    user_id: UUID


@dataclass
class InferenceAppInfo:
    endpoint_id: UUID


class Circuit(BaseModel):
    id: Annotated[UUID, Field(UUID, description="ID of circuit.")]

    app: Annotated[
        str,
        Field(
            str,
            description="Name of the Backend.AI Kernel app circuit is hosting. Can be a blank string if circuit is referencing an inference app.",
        ),
    ]
    protocol: Annotated[
        ProxyProtocol, Field(ProxyProtocol, description="Protocol of the Backend.AI Kernel app.")
    ]
    worker: Annotated[UUID, Field(UUID, description="ID of the worker hosting the circuit.")]

    app_mode: Annotated[AppMode, Field(AppMode, description="Application operation mode.")]
    frontend_mode: Annotated[
        FrontendMode, Field(FrontendMode, description="Frontend type of worker.")
    ]

    envs: dict[str, Any]
    arguments: str | None

    open_to_public: Annotated[
        bool,
        Field(
            bool,
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
            str | None,
            description="Comma separated list of CIDRs accepted as traffic source. null means the circuit is accessible anywhere.",
        ),
    ]

    port: Annotated[
        int,
        Field(int, description="Occupied worker port."),
    ]

    user_id: Annotated[UUID | None, Field(UUID | None, description="Session owner's UUID.")]
    access_key: Annotated[str | None, Field(str | None, description="Session owner's access key.")]
    endpoint_id: Annotated[
        UUID | None,
        Field(
            UUID | None, description="Model service's UUID. Only set if `app_mode` is inference."
        ),
    ]

    route_info: Annotated[
        list[RouteInfo], Field(list[RouteInfo], description="List of kernel access information.")
    ]
    session_ids: list[UUID]

    created_at: datetime
    updated_at: datetime

    @property
    def app_info(self) -> InteractiveAppInfo | InferenceAppInfo:
        match self.app_mode:
            case AppMode.INTERACTIVE:
                assert self.user_id
                return InteractiveAppInfo(self.user_id)
            case AppMode.INFERENCE:
                assert self.endpoint_id
                return InferenceAppInfo(self.endpoint_id)
            case _:
                raise KeyError(f"{self.app_mode} is not a valid app mode")


class Token(BaseModel):
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
    existing_url: AnyUrl | None


TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


@dataclass
class PydanticResponse(Generic[TBaseModel]):
    response: TBaseModel
    headers: dict[str, Any] = dataclasses.field(default_factory=lambda: {})
    status: int = 200


PERMIT_COOKIE_NAME: Final[str] = "appproxy_permit"

TCircuitKey = TypeVar("TCircuitKey", int, str)
