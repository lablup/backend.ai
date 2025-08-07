from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.appproxy.common.types import (
    FrontendMode,
    SerializableCircuit,
    SessionConfig,
)


class SlotModel(BaseModel):
    frontend_mode: FrontendMode
    in_use: bool
    port: Annotated[int | None, Field(default=None)]
    subdomain: Annotated[str | None, Field(default=None)]
    circuit_id: Annotated[UUID | None, Field(default=None)]
    """
    ID of circuit slot is hosting.
    """


class StubResponseModel(BaseModel):
    success: Annotated[bool, Field(default=True)]


class CircuitListResponseModel(BaseModel):
    circuits: list[SerializableCircuit]


class ConfRequestModel(BaseModel):
    login_session_token: str | None
    kernel_host: str
    kernel_port: int
    session: SessionConfig
