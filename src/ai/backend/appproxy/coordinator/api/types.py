import ipaddress
import re
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.appproxy.common.types import (
    FrontendMode,
    SerializableCircuit,
    SessionConfig,
)
from ai.backend.common.types import BackendAISchema

_KERNEL_HOST_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class SlotModel(BackendAISchema):
    frontend_mode: FrontendMode
    in_use: bool
    port: Annotated[int | None, Field(default=None)]
    subdomain: Annotated[str | None, Field(default=None)]
    circuit_id: Annotated[UUID | None, Field(default=None)]
    """
    ID of circuit slot is hosting.
    """


class StubResponseModel(BackendAISchema):
    success: Annotated[bool, Field(default=True)]


class CircuitListResponseModel(BackendAISchema):
    circuits: list[SerializableCircuit]


class ConfRequestModel(BackendAISchema):
    login_session_token: str | None
    kernel_host: Annotated[str, Field(max_length=255)]
    kernel_port: Annotated[int, Field(ge=1, le=65535)]
    session: SessionConfig

    @field_validator("kernel_host")
    @classmethod
    def _normalize_kernel_host(cls, value: str) -> str:
        # Routes are built as `http://{kernel_host}:{kernel_port}/`, so a value holding
        # a scheme, userinfo, port, path or query would point them at another host.
        try:
            return str(ipaddress.ip_address(value))
        except ValueError:
            pass
        if _KERNEL_HOST_NAME_PATTERN.fullmatch(value) is None:
            raise ValueError("kernel_host must be an IP address or a host name")
        return value
