"""DomainV2 GraphQL mutation input and payload types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.domain.request import (
    CreateDomainInput as CreateDomainInputDTO,
)
from ai.backend.common.dto.manager.v2.domain.request import (
    UpdateDomainInput as UpdateDomainInputDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DeleteDomainPayload as DeleteDomainPayloadDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainPayload as DomainPayloadDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    PurgeDomainPayload as PurgeDomainPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin

UNSET = None


# --- Inputs ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for creating a new domain.",
    )
)
class CreateDomainInputGQL(PydanticInputMixin[CreateDomainInputDTO]):
    """Input for creating a new domain."""

    name: str = gql_field(description="Domain name. Must be unique across the system.")
    description: str | None = gql_field(default=UNSET, description="Optional description.")
    is_active: bool = gql_field(default=True, description="Whether the domain is active.")
    allowed_docker_registries: list[str] | None = gql_field(
        default=UNSET, description="Allowed Docker registry URLs."
    )
    integration_id: str | None = gql_field(
        default=UNSET, description="External integration identifier."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating domain information. All fields optional.",
    )
)
class UpdateDomainInputGQL(PydanticInputMixin[UpdateDomainInputDTO]):
    """Input for updating domain information."""

    name: str | None = gql_field(default=UNSET, description="New domain name.")
    description: str | None = gql_field(default=UNSET, description="New description.")
    is_active: bool | None = gql_field(default=UNSET, description="Updated active status.")
    allowed_docker_registries: list[str] | None = gql_field(
        default=UNSET, description="New allowed Docker registry URLs."
    )
    integration_id: str | None = gql_field(
        default=UNSET, description="New external integration identifier."
    )


# --- Payloads ---


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for domain mutation responses.",
    ),
    model=DomainPayloadDTO,
)
class DomainPayloadGQL(PydanticOutputMixin[DomainPayloadDTO]):
    """Payload for domain create/update mutations."""

    domain: DomainV2GQL = gql_field(description="The domain entity.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for domain deletion mutation.",
    ),
    model=DeleteDomainPayloadDTO,
)
class DeleteDomainPayloadGQL(PydanticOutputMixin[DeleteDomainPayloadDTO]):
    """Payload for domain soft-delete."""

    deleted: bool = gql_field(description="Whether the deletion was successful.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for domain permanent deletion mutation.",
    ),
    model=PurgeDomainPayloadDTO,
)
class PurgeDomainPayloadGQL(PydanticOutputMixin[PurgeDomainPayloadDTO]):
    """Payload for domain permanent purge."""

    purged: bool = gql_field(description="Whether the purge was successful.")
