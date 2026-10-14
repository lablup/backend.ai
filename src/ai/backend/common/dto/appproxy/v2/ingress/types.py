"""Ingress: the routing state an AppProxy worker serves for one frontend."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import NewType, Self
from uuid import UUID

from pydantic import ConfigDict, Field, IPvAnyNetwork, model_validator

from ai.backend.common.api_handlers import BaseFieldModel
from ai.backend.common.exception import UnreachableError

IngressID = NewType("IngressID", str)
IngressAuthority = NewType("IngressAuthority", str)
IngressFrontendKey = NewType("IngressFrontendKey", str)
IngressBackendID = NewType("IngressBackendID", str)
IngressTargetGroupID = NewType("IngressTargetGroupID", str)
IngressTargetID = NewType("IngressTargetID", str)


class IngressFrontendKind(StrEnum):
    PORT = "port"
    WILDCARD = "wildcard"


class IngressProtocol(StrEnum):
    HTTP = "http"
    HTTP2 = "http2"
    TCP = "tcp"


class IngressAccessMode(StrEnum):
    PUBLIC = "public"
    USER = "user"
    TOKEN = "token"


class PortFrontend(BaseFieldModel):
    number: int = Field(ge=1, le=65535, description="Traffic port the worker listens on.")


class WildcardFrontend(BaseFieldModel):
    subdomain: str = Field(min_length=1, description="Subdomain under the wildcard domain.")


class IngressFrontend(BaseFieldModel):
    kind: IngressFrontendKind
    protocol: IngressProtocol
    port: PortFrontend | None = Field(default=None, description="Set only when kind is port.")
    wildcard: WildcardFrontend | None = Field(
        default=None, description="Set only when kind is wildcard."
    )

    @model_validator(mode="after")
    def _check_kind(self) -> Self:
        match self.kind:
            case IngressFrontendKind.PORT:
                if self.port is None or self.wildcard is not None:
                    raise ValueError("A port frontend sets port only")
            case IngressFrontendKind.WILDCARD:
                if self.wildcard is None or self.port is not None:
                    raise ValueError("A wildcard frontend sets wildcard only")
                if self.protocol == IngressProtocol.TCP:
                    raise ValueError("A wildcard frontend cannot carry tcp")
        return self

    def key(self) -> IngressFrontendKey:
        """The port number or the subdomain; unique within an authority."""
        if self.port is not None:
            return IngressFrontendKey(str(self.port.number))
        if self.wildcard is not None:
            return IngressFrontendKey(self.wildcard.subdomain)
        raise UnreachableError("A validated frontend sets either port or wildcard")


class IngressUserAccess(BaseFieldModel):
    open: bool = Field(default=False, description="Allows every identified user not denied.")
    allowed_user_ids: list[UUID] = Field(default_factory=list)
    denied_user_ids: list[UUID] = Field(
        default_factory=list, description="Rejected even when open or allowed."
    )

    @model_validator(mode="after")
    def _check_reachable(self) -> Self:
        if not self.open and not self.allowed_user_ids:
            raise ValueError("user access needs open or at least one allowed user")
        return self


class IngressTokenAccess(BaseFieldModel):
    pass


class IngressAccess(BaseFieldModel):
    mode: IngressAccessMode
    allowed_client_ips: list[IPvAnyNetwork] = Field(
        description="Client networks allowed to connect; empty allows any."
    )
    users: IngressUserAccess | None = Field(default=None, description="Required for user.")
    token: IngressTokenAccess | None = Field(default=None, description="Required for token.")

    @model_validator(mode="after")
    def _check_mode(self) -> Self:
        match self.mode:
            case IngressAccessMode.USER:
                if self.users is None:
                    raise ValueError("user access requires users")
            case IngressAccessMode.TOKEN:
                if self.token is None:
                    raise ValueError("token access requires token")
        return self


class IngressTarget(BaseFieldModel):
    id: IngressTargetID
    host: str
    port: int = Field(ge=1, le=65535)


class IngressTargetGroup(BaseFieldModel):
    id: IngressTargetGroupID
    weight: int = Field(ge=0)
    targets: list[IngressTarget]


class IngressBackend(BaseFieldModel):
    id: IngressBackendID
    target_groups: list[IngressTargetGroup] = Field(min_length=1)


class IngressKey(BaseFieldModel):
    model_config = ConfigDict(frozen=True)

    authority: IngressAuthority
    frontend_key: IngressFrontendKey


class Ingress(BaseFieldModel):
    model_config = ConfigDict(extra="ignore")

    id: IngressID
    authority: IngressAuthority = Field(
        description="Authority of the workers that serve this ingress."
    )
    revision: int = Field(ge=0, description="Raised on every change; a lower revision is stale.")
    frontend: IngressFrontend
    access: IngressAccess
    backend: IngressBackend

    @model_validator(mode="after")
    def _check_access_protocol(self) -> Self:
        if (
            self.access.mode != IngressAccessMode.PUBLIC
            and self.frontend.protocol != IngressProtocol.HTTP
        ):
            raise ValueError("user and token access are supported over http only")
        return self

    def key(self) -> IngressKey:
        return IngressKey(authority=self.authority, frontend_key=self.frontend.key())


@dataclass(frozen=True)
class IngressRedisKey:
    prefix: str

    def of(self, authority: IngressAuthority, frontend_key: IngressFrontendKey) -> str:
        return f"{self.prefix}:{authority}:{frontend_key}"

    def pattern(self, authority: IngressAuthority) -> str:
        """Matches every ingress key of the authority."""
        return f"{self.prefix}:{authority}:*"
