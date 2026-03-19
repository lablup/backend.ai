from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any, Self

import strawberry
from strawberry import ID, UNSET, Info
from strawberry.relay import Connection, Edge, NodeID
from strawberry.scalars import JSON

from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    VerificationStepResult,
    VerifierResult,
)
from ai.backend.common.data.storage.registries.types import ModelTarget as ModelTargetData
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactRevisionsInput,
    ArtifactGQLFilterInputDTO,
    ArtifactGQLOrderByInputDTO,
    ArtifactRevisionGQLFilterInputDTO,
    ArtifactRevisionGQLOrderByInputDTO,
    ArtifactRevisionRemoteStatusFilterDTO,
    ArtifactRevisionStatusFilterDTO,
    ArtifactStatusChangedInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    ApproveArtifactInput as ApproveArtifactInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    CancelImportTaskInput as CancelArtifactInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    CleanupRevisionsInput as CleanupArtifactRevisionsInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    DelegateeTargetInput as DelegateeTargetInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    DelegateImportArtifactsInput as DelegateImportArtifactsInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    DelegateScanArtifactsInput as DelegateScanArtifactsInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    DeleteArtifactsInput as DeleteArtifactsInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    ImportArtifactsInput as ImportArtifactsInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    ImportArtifactsOptionsInput as ImportArtifactsOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    ModelTargetInput as ModelTargetInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    RejectArtifactInput as RejectArtifactInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    RestoreArtifactsInput as RestoreArtifactsInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    ScanArtifactModelsInput as ScanArtifactModelsInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    ScanArtifactsInput as ScanArtifactsInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.request import (
    UpdateArtifactGQLInput as UpdateArtifactGQLInputDTO,
)
from ai.backend.common.dto.manager.v2.artifact.response import (
    ArtifactImportProgressUpdatedGQLPayload,
    ArtifactNode,
    ArtifactRevisionNode,
    ArtifactVerifierMetadataEntryDTO,
    SourceInfoDTO,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability as ArtifactAvailabilityDTO,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactOrderField as ArtifactOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactRemoteStatus as ArtifactRemoteStatusDTO,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactRevisionOrderField as ArtifactRevisionOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactStatus as ArtifactStatusDTO,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactType as ArtifactTypeDTO,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.manager.api.gql.base import (
    ByteSize,
    IntFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
    encode_cursor,
)
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactOrderField,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactRevisionOrderField,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.artifact.types import DelegateeTarget as DelegateeTargetData
from ai.backend.manager.defs import ARTIFACT_MAX_SCAN_LIMIT
from ai.backend.manager.errors.artifact_registry import ArtifactRegistryNotFoundError
from ai.backend.manager.models.artifact_revision.conditions import ArtifactRevisionConditions
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.artifact_revision.actions.get import GetArtifactRevisionAction


async def get_registry_url(
    data_loaders: DataLoaders,
    registry_id: uuid.UUID,
    registry_type: ArtifactRegistryType,
) -> str:
    """Get the URL for a registry based on its type."""
    match registry_type:
        case ArtifactRegistryType.HUGGINGFACE:
            hf_registry = await data_loaders.huggingface_registry_loader.load(registry_id)
            if hf_registry is None:
                raise ArtifactRegistryNotFoundError(f"HuggingFace registry {registry_id} not found")
            return hf_registry.url
        case ArtifactRegistryType.RESERVOIR:
            reservoir_registry = await data_loaders.reservoir_registry_loader.load(registry_id)
            if reservoir_registry is None:
                raise ArtifactRegistryNotFoundError(f"Reservoir registry {registry_id} not found")
            return reservoir_registry.endpoint
    raise ArtifactRegistryNotFoundError(f"Unknown registry type: {registry_type}")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="A single key-value entry representing metadata from an artifact verifier. Contains additional information about the verification process.",
    ),
    model=ArtifactVerifierMetadataEntryDTO,
    name="ArtifactVerifierMetadataEntry",
)
class ArtifactVerifierMetadataEntryGQL:
    key: strawberry.auto
    value: strawberry.auto


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description="A collection of metadata from an artifact verifier. Contains key-value pairs providing additional information about the verification.",
    ),
    name="ArtifactVerifierMetadata",
)
class ArtifactVerifierMetadataGQL:
    """Metadata containing multiple key-value entries."""

    entries: list[ArtifactVerifierMetadataEntryGQL] = strawberry.field(
        description="List of metadata entries. Each entry contains a key-value pair."
    )

    @classmethod
    def from_mapping(cls, data: Mapping[str, str]) -> ArtifactVerifierMetadataGQL:
        """Convert a Mapping to GraphQL type."""
        entries = [ArtifactVerifierMetadataEntryGQL(key=k, value=v) for k, v in data.items()]
        return cls(entries=entries)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.17.0",
        description="Result from a single malware verifier containing scan results and metadata. Each verifier scans the artifact for potential security issues and reports findings including infected file count, scan time, and any errors encountered.",
    ),
    name="ArtifactVerifierResult",
)
class ArtifactVerifierGQLResult:
    success: bool = strawberry.field(description="Whether the verification completed successfully")
    infected_count: int = strawberry.field(
        description="Number of infected or suspicious files detected"
    )
    scanned_at: datetime = strawberry.field(description="Timestamp when verification started")
    scan_time: float = strawberry.field(
        description="Time taken to complete verification in seconds"
    )
    scanned_count: int = strawberry.field(description="Total number of files scanned")
    metadata: ArtifactVerifierMetadataGQL = strawberry.field(
        description="Added in 26.1.0. Additional metadata from the verifier."
    )
    error: str | None = strawberry.field(
        description="Fatal error message if the verifier failed to complete"
    )

    @classmethod
    def from_dataclass(cls, data: VerifierResult) -> ArtifactVerifierGQLResult:
        return cls(
            success=data.success,
            infected_count=data.infected_count,
            scanned_at=data.scanned_at,
            scan_time=data.scan_time,
            scanned_count=data.scanned_count,
            metadata=ArtifactVerifierMetadataGQL.from_mapping(data.metadata),
            error=data.error,
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.17.0",
        description="Entry for a single verifier's result in the verification results. Associates a verifier name with its scan results.",
    ),
    name="ArtifactVerifierResultEntry",
)
class ArtifactVerifierGQLResultEntry:
    name: str = strawberry.field(description="Name of the verifier (e.g., 'clamav', 'custom')")
    result: ArtifactVerifierGQLResult = strawberry.field(
        description="Scan result from this verifier"
    )

    @classmethod
    def from_verifier_result(
        cls, name: str, result: VerifierResult
    ) -> ArtifactVerifierGQLResultEntry:
        return cls(
            name=name,
            result=ArtifactVerifierGQLResult.from_dataclass(result),
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.17.0",
        description="Complete verification result containing results from all configured verifiers. Artifacts undergo malware scanning through multiple verifiers after being imported. This type aggregates results from all verifiers that were run on the artifact.",
    ),
    name="ArtifactVerificationResult",
)
class ArtifactVerificationGQLResult:
    verifiers: list[ArtifactVerifierGQLResultEntry] = strawberry.field(
        description="Results from each verifier that scanned the artifact"
    )

    @classmethod
    def from_dataclass(cls, data: VerificationStepResult) -> ArtifactVerificationGQLResult:
        verifier_entries = [
            ArtifactVerifierGQLResultEntry.from_verifier_result(verifier_name, verifier_result)
            for verifier_name, verifier_result in data.verifiers.items()
        ]
        return cls(verifiers=verifier_entries)


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ArtifactGQLFilterInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Filter options for artifacts based on various criteria such as type, name, registry,
    source, and availability status.

    Supports logical operations (AND, OR, NOT) for complex filtering scenarios.
    """),
)
class ArtifactFilter(GQLFilter):
    type: list[ArtifactType] | None = None
    name: StringFilter | None = None
    registry: StringFilter | None = None
    source: StringFilter | None = None
    availability: list[ArtifactAvailability] | None = None

    AND: list[ArtifactFilter] | None = None
    OR: list[ArtifactFilter] | None = None
    NOT: list[ArtifactFilter] | None = None

    def to_pydantic(self) -> ArtifactGQLFilterInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ArtifactGQLFilterInputDTO(
            type=[ArtifactTypeDTO(t.value) for t in self.type] if self.type else None,
            name=self.name.to_pydantic() if self.name else None,
            registry=self.registry.to_pydantic() if self.registry else None,
            source=self.source.to_pydantic() if self.source else None,
            availability=(
                [ArtifactAvailabilityDTO(a.value) for a in self.availability]
                if self.availability
                else None
            ),
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ArtifactGQLOrderByInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Specifies the field and direction for ordering artifacts in queries.
    """),
)
class ArtifactOrderBy(GQLOrderBy):
    field: ArtifactOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> ArtifactGQLOrderByInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ArtifactGQLOrderByInputDTO(
            field=ArtifactOrderFieldDTO(self.field.value),
            direction=OrderDirectionDTO(self.direction.value),
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ArtifactRevisionStatusFilterDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Filter for artifact revision status. Supports exact match or inclusion in a list of statuses.
    """),
)
class ArtifactRevisionStatusFilter:
    in_: list[ArtifactStatus] | None = strawberry.field(name="in", default=None)
    equals: ArtifactStatus | None = None

    def to_pydantic(self) -> ArtifactRevisionStatusFilterDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ArtifactRevisionStatusFilterDTO(
            in_=[ArtifactStatusDTO(s.value) for s in self.in_] if self.in_ else None,
            equals=ArtifactStatusDTO(self.equals.value) if self.equals else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.16.0"),
    model=ArtifactRevisionRemoteStatusFilterDTO,
)
class ArtifactRevisionRemoteStatusFilter:
    in_: list[ArtifactRemoteStatus] | None = strawberry.field(name="in", default=None)
    equals: ArtifactRemoteStatus | None = None

    def to_pydantic(self) -> ArtifactRevisionRemoteStatusFilterDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ArtifactRevisionRemoteStatusFilterDTO(
            in_=[ArtifactRemoteStatusDTO(s.value) for s in self.in_] if self.in_ else None,
            equals=ArtifactRemoteStatusDTO(self.equals.value) if self.equals else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ArtifactRevisionGQLFilterInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Filter options for artifact revisions based on status, version, artifact ID, and file size.

    Supports logical operations (AND, OR, NOT) for complex filtering scenarios.
    """),
)
class ArtifactRevisionFilter(GQLFilter):
    status: ArtifactRevisionStatusFilter | None = None
    remote_status: ArtifactRevisionRemoteStatusFilter | None = strawberry.field(
        default=None, description="Added in 25.16.0"
    )
    version: StringFilter | None = None
    artifact_id: UUIDFilter | None = strawberry.field(default=None)
    size: IntFilter | None = None

    AND: list[ArtifactRevisionFilter] | None = None
    OR: list[ArtifactRevisionFilter] | None = None
    NOT: list[ArtifactRevisionFilter] | None = None

    def to_pydantic(self) -> ArtifactRevisionGQLFilterInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ArtifactRevisionGQLFilterInputDTO(
            status=(
                ArtifactRevisionStatusFilterDTO(
                    in_=[ArtifactStatusDTO(s.value) for s in self.status.in_]
                    if self.status.in_
                    else None,
                    equals=ArtifactStatusDTO(self.status.equals.value)
                    if self.status.equals
                    else None,
                )
                if self.status
                else None
            ),
            remote_status=(
                ArtifactRevisionRemoteStatusFilterDTO(
                    in_=[ArtifactRemoteStatusDTO(s.value) for s in self.remote_status.in_]
                    if self.remote_status.in_
                    else None,
                    equals=ArtifactRemoteStatusDTO(self.remote_status.equals.value)
                    if self.remote_status.equals
                    else None,
                )
                if self.remote_status
                else None
            ),
            version=self.version.to_pydantic() if self.version else None,
            artifact_id=self.artifact_id.to_pydantic() if self.artifact_id else None,
            size=self.size.to_pydantic() if self.size else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ArtifactRevisionGQLOrderByInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Specifies the field and direction for ordering artifact revisions in queries.
    """),
)
class ArtifactRevisionOrderBy(GQLOrderBy):
    field: ArtifactRevisionOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> ArtifactRevisionGQLOrderByInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ArtifactRevisionGQLOrderByInputDTO(
            field=ArtifactRevisionOrderFieldDTO(self.field.value),
            direction=OrderDirectionDTO(self.direction.value),
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ScanArtifactsInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Input for scanning artifacts from external registries (HuggingFace, Reservoir).

    Discovers available artifacts and registers their metadata in the system.
    Artifacts remain in SCANNED status until explicitly imported via import_artifacts.
    """),
)
class ScanArtifactsInput:
    registry_id: ID | None = None
    limit: int = strawberry.field(
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})"
    )
    artifact_type: ArtifactType | None = None
    search: str | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ImportArtifactsOptionsInputDTO,
    description=dedent_strip("""
    Added in 26.1.0.

    Options for importing artifact revisions.

    Controls import behavior such as forcing re-download regardless of digest freshness.
    """),
)
class ImportArtifactsOptionsGQL:
    force: bool = strawberry.field(
        default=False,
        description="Force re-download regardless of digest freshness check.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ImportArtifactsInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Input for importing scanned artifact revisions from external registries.

    Downloads artifact files from the external source and transitions them through:
    SCANNED → PULLING → PULLED → AVAILABLE status progression.
    """),
)
class ImportArtifactsInput:
    artifact_revision_ids: list[ID]
    vfolder_id: ID | None = strawberry.field(
        default=None,
        description="Target vfolder ID to store the imported artifacts. Added in 26.1.0.",
    )
    options: ImportArtifactsOptionsGQL | None = strawberry.field(
        default=None,
        description="Options controlling import behavior such as forcing re-download. Added in 26.1.0.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="25.15.0"),
    model=DelegateeTargetInputDTO,
)
class DelegateeTarget:
    delegatee_reservoir_id: ID
    target_registry_id: ID

    def to_dataclass(self) -> DelegateeTargetData:
        return DelegateeTargetData(
            delegatee_reservoir_id=uuid.UUID(self.delegatee_reservoir_id),
            target_registry_id=uuid.UUID(self.target_registry_id),
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=DelegateScanArtifactsInputDTO,
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for delegated scanning of artifacts from a delegatee reservoir registry's remote registry.
"""),
)
class DelegateScanArtifactsInput:
    delegator_reservoir_id: ID | None = strawberry.field(
        default=None, description="ID of the reservoir registry to delegate the scan request to"
    )
    delegatee_target: DelegateeTarget | None = strawberry.field(
        default=None,
        description="Target delegatee reservoir registry and its remote registry to scan",
    )
    limit: int = strawberry.field(
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})"
    )
    artifact_type: ArtifactType | None = strawberry.field(
        default=None, description="Filter artifacts by type (e.g., model, image, package)"
    )
    search: str | None = strawberry.field(
        default=None, description="Search term to filter artifacts by name or description"
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=DelegateImportArtifactsInputDTO,
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for delegated import of artifact revisions from a reservoir registry's remote registry.
    Used to specify which artifact revisions should be imported from the remote registry source
    into the local reservoir registry storage.
"""),
)
class DelegateImportArtifactsInput:
    artifact_revision_ids: list[ID] = strawberry.field(
        description="List of artifact revision IDs of delegatee artifact registry"
    )
    delegator_reservoir_id: ID | None = strawberry.field(
        default=None, description="ID of the reservoir registry to delegate the import request to"
    )
    artifact_type: ArtifactType | None = strawberry.field(default=None)
    delegatee_target: DelegateeTarget | None = strawberry.field(default=None)
    options: ImportArtifactsOptionsGQL | None = strawberry.field(
        default=None,
        description="Options controlling import behavior such as forcing re-download. Added in 26.1.0.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=UpdateArtifactGQLInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Input for updating artifact metadata properties.

    Modifies artifact metadata such as readonly status and description.
    This operation does not affect the actual artifact files or revisions.
    """),
)
class UpdateArtifactInput:
    artifact_id: ID
    readonly: bool | None = UNSET
    description: str | None = UNSET

    def to_pydantic(self) -> UpdateArtifactGQLInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return UpdateArtifactGQLInputDTO(
            artifact_id=uuid.UUID(self.artifact_id),
            readonly=self.readonly if self.readonly is not UNSET else None,
            description=self.description if self.description is not UNSET else None,
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=CancelArtifactInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Input for canceling an in-progress artifact import operation.

    Stops the download process and reverts the artifact revision status back to SCANNED.
    """),
)
class CancelArtifactInput:
    artifact_revision_id: ID


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=CleanupArtifactRevisionsInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Input for cleaning up stored artifact revision data.

    Removes downloaded files from storage and transitions the artifact revision
    back to SCANNED status, freeing up storage space.
    """),
)
class CleanupArtifactRevisionsInput:
    artifact_revision_ids: list[ID]


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=DeleteArtifactsInputDTO,
    description=dedent_strip("""
    Added in 25.15.0.

    Input for soft-deleting artifacts from the system.

    Marks artifacts as deleted without permanently removing them.
    Deleted artifacts can be restored using restore_artifacts.
    """),
)
class DeleteArtifactsInput:
    artifact_ids: list[ID]


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=RestoreArtifactsInputDTO,
    description=dedent_strip("""
    Added in 25.15.0.

    Input for restoring previously deleted artifacts.

    Reverses the soft-delete operation, making the artifacts available again.
    """),
)
class RestoreArtifactsInput:
    artifact_ids: list[ID]


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ApproveArtifactInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Input for approving an artifact revision.

    Admin-only operation to approve artifact revisions for general use.
    """),
)
class ApproveArtifactInput:
    artifact_revision_id: ID


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=RejectArtifactInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Input for rejecting an artifact revision.

    Admin-only operation to reject artifact revisions, preventing their use.
    """),
)
class RejectArtifactInput:
    artifact_revision_id: ID


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ArtifactStatusChangedInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Input for subscribing to artifact status change notifications.

    Used with artifact_status_changed subscription to receive real-time updates
    when artifact revision statuses change.
    """),
)
class ArtifactStatusChangedInput:
    artifact_revision_ids: list[ID]

    def to_pydantic(self) -> ArtifactStatusChangedInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ArtifactStatusChangedInputDTO(
            artifact_revision_ids=[uuid.UUID(id_) for id_ in self.artifact_revision_ids],
        )


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ModelTargetInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Specifies a target model for scanning operations.

    Used to identify specific models in external registries for detailed scanning.
    If revision is not specified, defaults to 'main' revision.
    """),
)
class ModelTarget:
    model_id: str
    revision: str | None = None

    def to_dataclass(self) -> ModelTargetData:
        return ModelTargetData(model_id=self.model_id, revision=self.revision)


@gql_pydantic_input(
    BackendAIGQLMeta(description="", added_version="24.09.0"),
    model=ScanArtifactModelsInputDTO,
    description=dedent_strip("""
    Added in 25.14.0.

    Input for batch scanning of specific models from external registries.

    Scans multiple specified models and retrieves detailed information including
    README content and file sizes. This operation performs immediate detailed scanning
    unlike the general scan_artifacts which only retrieves basic metadata.
    """),
)
class ScanArtifactModelsInput:
    models: list[ModelTarget]
    registry_id: uuid.UUID | None = None


# Object Types
@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Information about the source or registry of an artifact. Contains the name and URL of the registry where the artifact is stored or originates from.",
    ),
    model=SourceInfoDTO,
)
class SourceInfo:
    name: strawberry.auto
    url: strawberry.auto


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="An artifact represents AI models, packages, images, or other resources that can be stored, managed, and used within Backend.AI. Artifacts are discovered through scanning external registries and can have multiple revisions. Each artifact contains metadata and references to its source registry. Key concepts: Type (MODEL, PACKAGE, or IMAGE), Availability (ALIVE or DELETED), Source (original external registry where it was discovered).",
    ),
)
class Artifact(PydanticNodeMixin[ArtifactNode]):
    id: NodeID[str]
    name: str
    type: ArtifactType
    description: str | None
    registry: SourceInfo
    source: SourceInfo
    readonly: bool
    extra: JSON | None
    scanned_at: datetime
    updated_at: datetime
    availability: ArtifactAvailability

    @classmethod
    def from_dataclass(cls, data: ArtifactData, registry_url: str, source_url: str) -> Self:
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            type=ArtifactType(data.type),
            description=data.description,
            registry=SourceInfo(name=data.registry_type.value, url=registry_url),
            source=SourceInfo(name=data.source_registry_type.value, url=source_url),
            readonly=data.readonly,
            extra=data.extra,
            scanned_at=data.scanned_at,
            updated_at=data.updated_at,
            availability=data.availability,
        )

    @classmethod
    def from_artifact_node(cls, node: ArtifactNode, registry_url: str, source_url: str) -> Self:
        """Create from an ArtifactNode DTO (search result from adapter)."""
        return cls(
            id=ID(str(node.id)),
            name=node.name,
            type=ArtifactType(node.type.value),
            description=node.description,
            registry=SourceInfo(name=node.registry_type.value, url=registry_url),
            source=SourceInfo(name=node.source_registry_type.value, url=source_url),
            readonly=node.readonly,
            extra=node.extra,
            scanned_at=node.scanned_at,
            updated_at=node.updated_at,
            availability=ArtifactAvailability(node.availability.value),
        )

    @strawberry.field
    async def revisions(
        self,
        info: Info[StrawberryGQLContext],
        filter: ArtifactRevisionFilter | None = None,
        order_by: list[ArtifactRevisionOrderBy] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ArtifactRevisionConnection:
        pydantic_filter = filter.to_pydantic() if filter is not None else None
        pydantic_order = [o.to_pydantic() for o in order_by] if order_by is not None else None

        base_conditions = [ArtifactRevisionConditions.by_artifact_id(uuid.UUID(self.id))]

        search_input = AdminSearchArtifactRevisionsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        payload = await info.context.adapters.artifact.search_revisions_gql(
            search_input,
            base_conditions=base_conditions,
        )

        edges = []
        for item in payload.items:
            revision = ArtifactRevision(
                id=ID(str(item.id)),
                status=ArtifactStatus(item.status.value),
                remote_status=ArtifactRemoteStatus(item.remote_status)
                if item.remote_status
                else None,
                readme=None,
                version=item.version,
                size=ByteSize(item.size) if item.size is not None else None,
                created_at=item.created_at,
                updated_at=item.updated_at,
                digest=None,
                verification_result=None,
            )
            cursor = encode_cursor(item.id)
            edges.append(ArtifactRevisionEdge(node=revision, cursor=cursor))

        page_info = strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )

        return ArtifactRevisionConnection(
            count=payload.total_count,
            edges=edges,
            page_info=page_info,
        )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="A specific version/revision of an artifact containing the actual file data. Artifact revisions progress through different statuses: SCANNED (discovered in external registry, metadata only), PULLING (currently downloading from external source), PULLED (downloaded to temporary storage), AVAILABLE (ready for use by users). Contains version information, file size, README content, and timestamps. Most HuggingFace models only have a 'main' revision.",
    ),
)
class ArtifactRevision(PydanticNodeMixin[ArtifactRevisionNode]):
    id: NodeID[str]
    status: ArtifactStatus
    remote_status: ArtifactRemoteStatus | None = strawberry.field(description="Added in 25.15.0")
    version: str
    readme: str | None
    size: ByteSize | None
    created_at: datetime | None
    updated_at: datetime | None
    digest: str | None = strawberry.field(
        description="Digest at the time of import. None for models that have not been imported. Added in 25.17.0"
    )
    verification_result: ArtifactVerificationGQLResult | None = strawberry.field(
        description="Verification result containing malware scan results from all verifiers. None if not yet verified. Added in 25.17.0"
    )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.artifact_revision_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @classmethod
    def from_dataclass(cls, data: ArtifactRevisionData) -> Self:
        return cls(
            id=ID(str(data.id)),
            status=ArtifactStatus(data.status),
            remote_status=ArtifactRemoteStatus(data.remote_status) if data.remote_status else None,
            readme=data.readme,
            version=data.version,
            size=ByteSize(data.size) if data.size is not None else None,
            created_at=data.created_at,
            updated_at=data.updated_at,
            digest=data.digest,
            verification_result=ArtifactVerificationGQLResult.from_dataclass(
                data.verification_result
            )
            if data.verification_result
            else None,
        )

    @strawberry.field
    async def artifact(self, info: Info[StrawberryGQLContext]) -> Artifact:
        revision_action_result = (
            await info.context.processors.artifact_revision.get.wait_for_complete(
                GetArtifactRevisionAction(artifact_revision_id=uuid.UUID(self.id))
            )
        )

        artifact_id = revision_action_result.revision.artifact_id

        artifact_action_result = await info.context.processors.artifact.get.wait_for_complete(
            GetArtifactAction(artifact_id=artifact_id)
        )

        data_loaders = info.context.data_loaders
        registry_url = await get_registry_url(
            data_loaders,
            artifact_action_result.result.registry_id,
            artifact_action_result.result.registry_type,
        )
        source_url = await get_registry_url(
            data_loaders,
            artifact_action_result.result.source_registry_id,
            artifact_action_result.result.source_registry_type,
        )

        return Artifact.from_dataclass(artifact_action_result.result, registry_url, source_url)


def make_artifact_from_node(node: ArtifactNode, registry_url: str, source_url: str) -> Artifact:
    """Create an Artifact GQL type from an ArtifactNode DTO (search result)."""
    return Artifact(
        id=ID(str(node.id)),
        name=node.name,
        type=ArtifactType(node.type.value),
        description=node.description,
        registry=SourceInfo(name=node.registry_type.value, url=registry_url),
        source=SourceInfo(name=node.source_registry_type.value, url=source_url),
        readonly=node.readonly,
        extra=node.extra,
        scanned_at=node.scanned_at,
        updated_at=node.updated_at,
        availability=ArtifactAvailability(node.availability.value),
    )


def make_artifact_revision_from_node(node: ArtifactRevisionNode) -> ArtifactRevision:
    """Create an ArtifactRevision GQL type from an ArtifactRevisionNode DTO (search result)."""
    return ArtifactRevision(
        id=ID(str(node.id)),
        status=ArtifactStatus(node.status.value),
        remote_status=ArtifactRemoteStatus(node.remote_status) if node.remote_status else None,
        readme=None,
        version=node.version,
        size=ByteSize(node.size) if node.size is not None else None,
        created_at=node.created_at,
        updated_at=node.updated_at,
        digest=None,
        verification_result=None,
    )


ArtifactEdge = Edge[Artifact]
ArtifactRevisionEdge = Edge[ArtifactRevision]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Paginated connection for artifacts with total count information. Used for relay-style pagination with cursor-based navigation.",
    ),
)
class ArtifactConnection(Connection[Artifact]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Paginated connection for artifact revisions with total count information. Used for relay-style pagination with cursor-based navigation.",
    ),
)
class ArtifactRevisionConnection(Connection[ArtifactRevision]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for artifact import progress subscription events. Provides real-time updates during the artifact import process, including progress percentage and current status.",
    ),
    model=ArtifactImportProgressUpdatedGQLPayload,
)
class ArtifactImportProgressUpdatedPayload:
    artifact_id: ID = strawberry.field(description="Artifact revision ID.")
    progress: float = strawberry.field(description="Import progress as a percentage.")
    status: ArtifactStatus = strawberry.field(description="Current import status.")


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Response payload for artifact scanning operations. Contains the list of artifacts discovered during scanning of external registries. These artifacts are registered with SCANNED status and can be imported for actual use.",
    ),
)
class ScanArtifactsPayload:
    artifacts: list[Artifact]


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Response payload for delegated artifact scanning operation. Contains the list of artifacts discovered during the scan of a reservoir registry's remote registry. These artifacts are now available for import or direct use.",
    ),
)
class DelegateScanArtifactsPayload:
    artifacts: list[Artifact] = strawberry.field(
        description="List of artifacts discovered during the delegated scan from the reservoir registry's remote registry"
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Represents a background task for importing an artifact revision. Contains the task ID for monitoring progress and the associated artifact revision being imported from external registries.",
    ),
)
class ArtifactRevisionImportTask:
    task_id: ID | None
    artifact_revision: ArtifactRevision


# Mutation Payloads
@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Response payload for artifact import operations. Contains the imported artifact revisions and their associated background tasks. Tasks can be monitored to track the import progress from SCANNED to AVAILABLE status.",
    ),
)
class ImportArtifactsPayload:
    artifact_revisions: ArtifactRevisionConnection
    tasks: list[ArtifactRevisionImportTask]


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Response payload for delegated artifact import operation. Contains the imported artifact revisions and associated background tasks. The tasks can be monitored to track the progress of the import operation.",
    ),
)
class DelegateImportArtifactsPayload:
    artifact_revisions: ArtifactRevisionConnection = strawberry.field(
        description="Connection of artifact revisions that were imported from the reservoir registry's remote registry"
    )
    tasks: list[ArtifactRevisionImportTask] = strawberry.field(
        description="List of background tasks created for importing the artifact revisions"
    )


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Response payload for artifact update operations. Returns the updated artifact with modified metadata properties.",
    ),
)
class UpdateArtifactPayload:
    artifact: Artifact


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Response payload for artifact revision cleanup operations. Contains the cleaned artifact revisions that have had their stored data removed, transitioning them back to SCANNED status to free storage space.",
    ),
)
class CleanupArtifactRevisionsPayload:
    artifact_revisions: ArtifactRevisionConnection


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Response payload for artifact revision approval operations. Contains the approved artifact revision. Admin-only operation.",
    ),
)
class ApproveArtifactPayload:
    artifact_revision: ArtifactRevision


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Response payload for artifact revision rejection operations. Contains the rejected artifact revision. Admin-only operation.",
    ),
)
class RejectArtifactPayload:
    artifact_revision: ArtifactRevision


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Response payload for canceling artifact import operations. Contains the artifact revision whose import was canceled, reverting its status back to SCANNED.",
    ),
)
class CancelImportArtifactPayload:
    artifact_revision: ArtifactRevision


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Payload for artifact status change subscription events. Provides real-time notifications when artifact revision statuses change during import, cleanup, or other operations.",
    ),
)
class ArtifactStatusChangedPayload:
    artifact_revision: ArtifactRevision


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.14.0",
        description="Response payload for batch model scanning operations. Contains the artifact revisions discovered during detailed scanning of specific models, including README content and file size information.",
    ),
)
class ScanArtifactModelsPayload:
    artifact_revision: ArtifactRevisionConnection


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Response payload for artifact deletion operations. Contains the artifacts that were soft-deleted. These can be restored later.",
    ),
)
class DeleteArtifactsPayload:
    artifacts: list[Artifact]


@gql_node_type(
    BackendAIGQLMeta(
        added_version="25.15.0",
        description="Response payload for artifact restoration operations. Contains the artifacts that were restored from soft-deleted state.",
    ),
)
class RestoreArtifactsPayload:
    artifacts: list[Artifact]
