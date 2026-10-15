"""DomainV2 GraphQL mutation input and payload types."""

from __future__ import annotations

from uuid import UUID

from strawberry import UNSET

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.domain.request import (
    CreateDomainInput as CreateDomainInputDTO,
)
from ai.backend.common.dto.manager.v2.domain.request import (
    PartialBulkDeleteDomainsInput as PartialBulkDeleteDomainsInputDTO,
)
from ai.backend.common.dto.manager.v2.domain.request import (
    PartialBulkRestoreDomainsInput as PartialBulkRestoreDomainsInputDTO,
)
from ai.backend.common.dto.manager.v2.domain.request import (
    PartialBulkUpdateDomainItemInput as PartialBulkUpdateDomainItemInputDTO,
)
from ai.backend.common.dto.manager.v2.domain.request import (
    PartialBulkUpdateDomainsInput as PartialBulkUpdateDomainsInputDTO,
)
from ai.backend.common.dto.manager.v2.domain.request import (
    UpdateDomainInput as UpdateDomainInputDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DeleteDomainPayload as DeleteDomainPayloadDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainNode,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    DomainPayload as DomainPayloadDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    PurgeDomainPayload as PurgeDomainPayloadDTO,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    RestoreDomainPayload as RestoreDomainPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import PartialBulkFailureGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin

# --- Inputs ---


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for creating a new domain.",
    ),
    name="CreateDomainInput",
)
class CreateDomainInputGQL(PydanticInputMixin[CreateDomainInputDTO]):
    """Input for creating a new domain."""

    name: str = gql_field(description="Domain name. Must be unique across the system.")
    description: str | None = gql_field(default=None, description="Optional description.")
    is_active: bool = gql_field(default=True, description="Whether the domain is active.")
    allowed_docker_registries: list[str] | None = gql_field(
        default=None, description="Allowed Docker registry URLs."
    )
    integration_name: str | None = gql_field(
        default=None, description="External integration identifier."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Input for updating domain information. All fields optional.",
    ),
    name="UpdateDomainInput",
)
class UpdateDomainInputGQL(PydanticInputMixin[UpdateDomainInputDTO]):
    """Input for updating domain information."""

    name: str | None = gql_field(default=UNSET, description="New domain name.")
    description: str | None = gql_field(default=UNSET, description="New description.")
    is_active: bool | None = gql_field(
        default=UNSET,
        description="Updated active status.",
        deprecation_reason=(
            f"Deprecated since {NEXT_RELEASE_VERSION}. Use `deleteDomainV2` or `restoreDomainV2`."
        ),
    )
    allowed_docker_registries: list[str] | None = gql_field(
        default=UNSET, description="New allowed Docker registry URLs."
    )
    integration_name: str | None = gql_field(
        default=UNSET, description="New external integration identifier."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One domain of a partial bulk update and the fields to update on it.",
    ),
    name="PartialBulkUpdateDomainItemInput",
)
class PartialBulkUpdateDomainItemInputGQL(PydanticInputMixin[PartialBulkUpdateDomainItemInputDTO]):
    id: UUID = gql_field(description="ID of the domain to update.")
    input: UpdateDomainInputGQL = gql_field(description="Fields to update on the domain.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for updating several domains, each answered for separately.",
    ),
    name="PartialBulkUpdateDomainsInput",
)
class PartialBulkUpdateDomainsInputGQL(PydanticInputMixin[PartialBulkUpdateDomainsInputDTO]):
    items: list[PartialBulkUpdateDomainItemInputGQL] = gql_field(
        description="The domains to update, each with its fields."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for soft-deleting several domains, each answered for separately.",
    ),
    name="PartialBulkDeleteDomainsInput",
)
class PartialBulkDeleteDomainsInputGQL(PydanticInputMixin[PartialBulkDeleteDomainsInputDTO]):
    ids: list[UUID] = gql_field(description="IDs of the domains to soft-delete.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for restoring several soft-deleted domains, each answered for separately."
        ),
    ),
    name="PartialBulkRestoreDomainsInput",
)
class PartialBulkRestoreDomainsInputGQL(PydanticInputMixin[PartialBulkRestoreDomainsInputDTO]):
    ids: list[UUID] = gql_field(description="IDs of the domains to restore.")


# --- Payloads ---


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for domain mutation responses.",
    ),
    model=DomainPayloadDTO,
    name="DomainPayload",
)
class DomainPayloadGQL(PydanticOutputMixin[DomainPayloadDTO]):
    """Payload for domain create/update mutations."""

    domain: DomainV2GQL = gql_field(description="The domain entity.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for domain deletion mutation.",
    ),
    model=DeleteDomainPayloadDTO,
    name="DeleteDomainPayload",
)
class DeleteDomainPayloadGQL(PydanticOutputMixin[DeleteDomainPayloadDTO]):
    """Payload for domain soft-delete."""

    deleted: bool = gql_field(description="Whether the deletion was successful.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.9.0",
        description="Payload for domain restore mutation.",
    ),
    model=RestoreDomainPayloadDTO,
    name="RestoreDomainPayload",
)
class RestoreDomainPayloadGQL(PydanticOutputMixin[RestoreDomainPayloadDTO]):
    """Payload for domain restore."""

    restored: bool = gql_field(description="Whether the restore was successful.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Payload for domain permanent deletion mutation.",
    ),
    model=PurgeDomainPayloadDTO,
    name="PurgeDomainPayload",
)
class PurgeDomainPayloadGQL(PydanticOutputMixin[PurgeDomainPayloadDTO]):
    """Payload for domain permanent purge."""

    purged: bool = gql_field(description="Whether the purge was successful.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk domain operation: the domains processed and the ones "
            "that failed."
        ),
    ),
    model=PartialBulkPayload[DomainNode],
    name="PartialBulkDomainsPayload",
)
class PartialBulkDomainsPayloadGQL(PydanticOutputMixin[PartialBulkPayload[DomainNode]]):
    """Payload for partial bulk domain mutations."""

    successes: list[DomainV2GQL] = gql_field(
        description="The domains processed, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The domains not processed, each with the reason."
    )
