from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Self

import strawberry
from aiotools import apartial
from strawberry import ID, UNSET, Info
from strawberry.dataloader import DataLoader
from strawberry.relay import Connection, Edge, Node, NodeID
from strawberry.scalars import JSON

from ai.backend.common.data.artifact.types import (
    VerificationStepResult,
    VerifierResult,
)
from ai.backend.common.data.storage.registries.types import ModelTarget as ModelTargetData
from ai.backend.manager.api.gql.base import (
    ByteSize,
    IntFilter,
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactFilterOptions,
    ArtifactOrderField,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactRevisionOrderField,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.artifact.types import DelegateeTarget as DelegateeTargetData
from ai.backend.manager.defs import ARTIFACT_MAX_SCAN_LIMIT
from ai.backend.manager.repositories.artifact.options import (
    ArtifactConditions,
    ArtifactOrders,
    ArtifactRevisionConditions,
    ArtifactRevisionOrders,
)
from ai.backend.manager.repositories.artifact.types import (
    ArtifactRemoteStatusFilter,
    ArtifactRemoteStatusFilterType,
    ArtifactRevisionFilterOptions,
    ArtifactStatusFilter,
    ArtifactStatusFilterType,
)
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.artifact.actions.get import GetArtifactAction
from ai.backend.manager.services.artifact_revision.actions.get import GetArtifactRevisionAction

from ..artifact_registry_meta import ArtifactRegistryMeta


@strawberry.type(
    name="ArtifactVerifierResult",
    description=dedent_strip("""
    Added in 25.17.0.

    Result from a single malware verifier containing scan results and metadata.

    Each verifier scans the artifact for potential security issues and reports
    findings including infected file count, scan time, and any errors encountered.
    """),
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
    metadata: JSON = strawberry.field(description="Additional metadata from the verifier")
    error: Optional[str] = strawberry.field(
        description="Fatal error message if the verifier failed to complete"
    )

    @classmethod
    def from_dataclass(cls, data: VerifierResult) -> Self:
        return cls(
            success=data.success,
            infected_count=data.infected_count,
            scanned_at=data.scanned_at,
            scan_time=data.scan_time,
            scanned_count=data.scanned_count,
            metadata=data.metadata,
            error=data.error,
        )


@strawberry.type(
    name="ArtifactVerifierResultEntry",
    description=dedent_strip("""
    Added in 25.17.0.

    Entry for a single verifier's result in the verification results.

    Associates a verifier name with its scan results.
    """),
)
class ArtifactVerifierGQLResultEntry:
    name: str = strawberry.field(description="Name of the verifier (e.g., 'clamav', 'custom')")
    result: ArtifactVerifierGQLResult = strawberry.field(
        description="Scan result from this verifier"
    )

    @classmethod
    def from_verifier_result(cls, name: str, result: VerifierResult) -> Self:
        return cls(
            name=name,
            result=ArtifactVerifierGQLResult.from_dataclass(result),
        )


@strawberry.type(
    name="ArtifactVerificationResult",
    description=dedent_strip("""
    Added in 25.17.0.

    Complete verification result containing results from all configured verifiers.

    Artifacts undergo malware scanning through multiple verifiers after being imported.
    This type aggregates results from all verifiers that were run on the artifact.
    """),
)
class ArtifactVerificationGQLResult:
    verifiers: list[ArtifactVerifierGQLResultEntry] = strawberry.field(
        description="Results from each verifier that scanned the artifact"
    )

    @classmethod
    def from_dataclass(cls, data: VerificationStepResult) -> Self:
        verifier_entries = [
            ArtifactVerifierGQLResultEntry.from_verifier_result(verifier_name, verifier_result)
            for verifier_name, verifier_result in data.verifiers.items()
        ]
        return cls(verifiers=verifier_entries)


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Filter options for artifacts based on various criteria such as type, name, registry,
    source, and availability status.

    Supports logical operations (AND, OR, NOT) for complex filtering scenarios.
    """)
)
class ArtifactFilter(GQLFilter):
    type: Optional[list[ArtifactType]] = None
    name: Optional[StringFilter] = None
    registry: Optional[StringFilter] = None
    source: Optional[StringFilter] = None
    availability: Optional[list[ArtifactAvailability]] = None

    AND: Optional[list["ArtifactFilter"]] = None
    OR: Optional[list["ArtifactFilter"]] = None
    NOT: Optional[list["ArtifactFilter"]] = None

    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list containing QueryConditions that represent
        all filters with proper logical operators applied.
        """
        # Collect direct field conditions (these will be combined with AND)
        field_conditions: list[QueryCondition] = []

        # Apply type filter
        if self.type:
            field_conditions.append(ArtifactConditions.by_types(self.type))

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=ArtifactConditions.by_name_contains,
                equals_factory=ArtifactConditions.by_name_equals,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply registry filter
        if self.registry:
            registry_condition = self.registry.build_query_condition(
                contains_factory=ArtifactConditions.by_registry_contains,
                equals_factory=ArtifactConditions.by_registry_equals,
            )
            if registry_condition:
                field_conditions.append(registry_condition)

        # Apply source filter
        if self.source:
            source_condition = self.source.build_query_condition(
                contains_factory=ArtifactConditions.by_source_contains,
                equals_factory=ArtifactConditions.by_source_equals,
            )
            if source_condition:
                field_conditions.append(source_condition)

        # Apply availability filter
        if self.availability:
            field_conditions.append(ArtifactConditions.by_availability(self.availability))

        # Handle AND logical operator - these are implicitly ANDed with field conditions
        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions

    def to_repo_filter(self) -> ArtifactFilterOptions:
        repo_filter = ArtifactFilterOptions()

        # Handle basic filters
        repo_filter.artifact_type = self.type
        repo_filter.name_filter = self.name.to_dataclass() if self.name else None
        repo_filter.registry_filter = self.registry.to_dataclass() if self.registry else None
        repo_filter.source_filter = self.source.to_dataclass() if self.source else None
        repo_filter.availability = self.availability

        # Handle logical operations
        if self.AND:
            repo_filter.AND = [f.to_repo_filter() for f in self.AND]
        if self.OR:
            repo_filter.OR = [f.to_repo_filter() for f in self.OR]
        if self.NOT:
            repo_filter.NOT = [f.to_repo_filter() for f in self.NOT]

        return repo_filter


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Specifies the field and direction for ordering artifacts in queries.
    """)
)
class ArtifactOrderBy(GQLOrderBy):
    field: ArtifactOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ArtifactOrderField.NAME:
                return ArtifactOrders.name(ascending)
            case ArtifactOrderField.TYPE:
                return ArtifactOrders.type(ascending)
            case ArtifactOrderField.SCANNED_AT:
                return ArtifactOrders.scanned_at(ascending)
            case ArtifactOrderField.UPDATED_AT:
                return ArtifactOrders.updated_at(ascending)


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Filter for artifact revision status. Supports exact match or inclusion in a list of statuses.
    """)
)
class ArtifactRevisionStatusFilter:
    in_: Optional[list[ArtifactStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ArtifactStatus] = None


@strawberry.input(description="Added in 25.16.0")
class ArtifactRevisionRemoteStatusFilter:
    in_: Optional[list[ArtifactRemoteStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[ArtifactRemoteStatus] = None


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Filter options for artifact revisions based on status, version, artifact ID, and file size.

    Supports logical operations (AND, OR, NOT) for complex filtering scenarios.
    """)
)
class ArtifactRevisionFilter(GQLFilter):
    status: Optional[ArtifactRevisionStatusFilter] = None
    remote_status: Optional[ArtifactRevisionRemoteStatusFilter] = strawberry.field(
        default=None, description="Added in 25.16.0"
    )
    version: Optional[StringFilter] = None
    artifact_id: Optional[ID] = None
    size: Optional[IntFilter] = None

    AND: Optional[list["ArtifactRevisionFilter"]] = None
    OR: Optional[list["ArtifactRevisionFilter"]] = None
    NOT: Optional[list["ArtifactRevisionFilter"]] = None

    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list containing QueryConditions that represent
        all filters with proper logical operators applied.
        """
        # Collect direct field conditions (these will be combined with AND)
        field_conditions: list[QueryCondition] = []

        # Apply status filter
        if self.status:
            statuses_to_filter: list[ArtifactStatus] = []
            if self.status.in_:
                statuses_to_filter = self.status.in_
            elif self.status.equals:
                statuses_to_filter = [self.status.equals]

            if statuses_to_filter:
                field_conditions.append(ArtifactRevisionConditions.by_statuses(statuses_to_filter))

        # Apply remote_status filter
        if self.remote_status:
            remote_statuses_to_filter: list[ArtifactRemoteStatus] = []
            if self.remote_status.in_:
                remote_statuses_to_filter = self.remote_status.in_
            elif self.remote_status.equals:
                remote_statuses_to_filter = [self.remote_status.equals]

            if remote_statuses_to_filter:
                field_conditions.append(
                    ArtifactRevisionConditions.by_remote_statuses(remote_statuses_to_filter)
                )

        # Apply version filter
        if self.version:
            version_condition = self.version.build_query_condition(
                contains_factory=ArtifactRevisionConditions.by_version_contains,
                equals_factory=ArtifactRevisionConditions.by_version_equals,
            )
            if version_condition:
                field_conditions.append(version_condition)

        # Apply size filter
        if self.size:
            if self.size.equals is not None:
                field_conditions.append(ArtifactRevisionConditions.by_size_equals(self.size.equals))
            elif self.size.not_equals is not None:
                field_conditions.append(
                    ArtifactRevisionConditions.by_size_not_equals(self.size.not_equals)
                )
            elif self.size.greater_than is not None:
                field_conditions.append(
                    ArtifactRevisionConditions.by_size_greater_than(self.size.greater_than)
                )
            elif self.size.greater_than_or_equal is not None:
                field_conditions.append(
                    ArtifactRevisionConditions.by_size_greater_than_or_equal(
                        self.size.greater_than_or_equal
                    )
                )
            elif self.size.less_than is not None:
                field_conditions.append(
                    ArtifactRevisionConditions.by_size_less_than(self.size.less_than)
                )
            elif self.size.less_than_or_equal is not None:
                field_conditions.append(
                    ArtifactRevisionConditions.by_size_less_than_or_equal(
                        self.size.less_than_or_equal
                    )
                )

        # Handle AND logical operator - these are implicitly ANDed with field conditions
        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions

    def to_repo_filter(self) -> ArtifactRevisionFilterOptions:
        repo_filter = ArtifactRevisionFilterOptions()

        # Handle basic filters
        if self.artifact_id:
            repo_filter.artifact_id = uuid.UUID(self.artifact_id)

        # Handle status filter using ArtifactRevisionStatusFilter
        if self.status:
            if self.status.in_:
                repo_filter.status_filter = ArtifactStatusFilter(
                    type=ArtifactStatusFilterType.IN, values=self.status.in_
                )
            elif self.status.equals:
                repo_filter.status_filter = ArtifactStatusFilter(
                    type=ArtifactStatusFilterType.EQUALS, values=[self.status.equals]
                )

        # Handle remote_status filter using ArtifactRevisionRemoteStatusFilter
        if self.remote_status:
            if self.remote_status.in_:
                repo_filter.remote_status_filter = ArtifactRemoteStatusFilter(
                    type=ArtifactRemoteStatusFilterType.IN, values=self.remote_status.in_
                )
            elif self.remote_status.equals:
                repo_filter.remote_status_filter = ArtifactRemoteStatusFilter(
                    type=ArtifactRemoteStatusFilterType.EQUALS, values=[self.remote_status.equals]
                )

        # Pass StringFilter directly for processing in repository
        repo_filter.version_filter = self.version

        # Handle size filter
        repo_filter.size_filter = self.size

        # Handle logical operations
        if self.AND:
            repo_filter.AND = [f.to_repo_filter() for f in self.AND]
        if self.OR:
            repo_filter.OR = [f.to_repo_filter() for f in self.OR]
        if self.NOT:
            repo_filter.NOT = [f.to_repo_filter() for f in self.NOT]

        return repo_filter


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Specifies the field and direction for ordering artifact revisions in queries.
    """)
)
class ArtifactRevisionOrderBy(GQLOrderBy):
    field: ArtifactRevisionOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ArtifactRevisionOrderField.VERSION:
                return ArtifactRevisionOrders.version(ascending)
            case ArtifactRevisionOrderField.STATUS:
                return ArtifactRevisionOrders.status(ascending)
            case ArtifactRevisionOrderField.SIZE:
                return ArtifactRevisionOrders.size(ascending)
            case ArtifactRevisionOrderField.CREATED_AT:
                return ArtifactRevisionOrders.created_at(ascending)
            case ArtifactRevisionOrderField.UPDATED_AT:
                return ArtifactRevisionOrders.updated_at(ascending)


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Input for scanning artifacts from external registries (HuggingFace, Reservoir).

    Discovers available artifacts and registers their metadata in the system.
    Artifacts remain in SCANNED status until explicitly imported via import_artifacts.
    """)
)
class ScanArtifactsInput:
    registry_id: Optional[ID] = None
    limit: int = strawberry.field(
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})"
    )
    artifact_type: Optional[ArtifactType] = None
    search: Optional[str] = None


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Input for importing scanned artifact revisions from external registries.

    Downloads artifact files from the external source and transitions them through:
    SCANNED → PULLING → PULLED → AVAILABLE status progression.
    """)
)
class ImportArtifactsInput:
    artifact_revision_ids: list[ID]


@strawberry.input(description="Added in 25.15.0")
class DelegateeTarget:
    delegatee_reservoir_id: ID
    target_registry_id: ID

    def to_dataclass(self) -> DelegateeTargetData:
        return DelegateeTargetData(
            delegatee_reservoir_id=uuid.UUID(self.delegatee_reservoir_id),
            target_registry_id=uuid.UUID(self.target_registry_id),
        )


@strawberry.input(
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for delegated scanning of artifacts from a delegatee reservoir registry's remote registry.
""")
)
class DelegateScanArtifactsInput:
    delegator_reservoir_id: Optional[ID] = strawberry.field(
        default=None, description="ID of the reservoir registry to delegate the scan request to"
    )
    delegatee_target: Optional[DelegateeTarget] = strawberry.field(
        default=None,
        description="Target delegatee reservoir registry and its remote registry to scan",
    )
    limit: int = strawberry.field(
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})"
    )
    artifact_type: Optional[ArtifactType] = strawberry.field(
        default=None, description="Filter artifacts by type (e.g., model, image, package)"
    )
    search: Optional[str] = strawberry.field(
        default=None, description="Search term to filter artifacts by name or description"
    )


@strawberry.input(
    description=dedent_strip("""
    Added in 25.15.0.

    Input type for delegated import of artifact revisions from a reservoir registry's remote registry.
    Used to specify which artifact revisions should be imported from the remote registry source
    into the local reservoir registry storage.
""")
)
class DelegateImportArtifactsInput:
    artifact_revision_ids: list[ID] = strawberry.field(
        description="List of artifact revision IDs of delegatee artifact registry"
    )
    delegator_reservoir_id: Optional[ID] = strawberry.field(
        default=None, description="ID of the reservoir registry to delegate the import request to"
    )
    artifact_type: Optional[ArtifactType] = strawberry.field(default=None)
    delegatee_target: Optional[DelegateeTarget] = strawberry.field(default=None)


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Input for updating artifact metadata properties.

    Modifies artifact metadata such as readonly status and description.
    This operation does not affect the actual artifact files or revisions.
    """)
)
class UpdateArtifactInput:
    artifact_id: ID
    readonly: Optional[bool] = UNSET
    description: Optional[str] = UNSET


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Input for canceling an in-progress artifact import operation.

    Stops the download process and reverts the artifact revision status back to SCANNED.
    """)
)
class CancelArtifactInput:
    artifact_revision_id: ID


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Input for cleaning up stored artifact revision data.

    Removes downloaded files from storage and transitions the artifact revision
    back to SCANNED status, freeing up storage space.
    """)
)
class CleanupArtifactRevisionsInput:
    artifact_revision_ids: list[ID]


@strawberry.input(
    description=dedent_strip("""
    Added in 25.15.0.

    Input for soft-deleting artifacts from the system.

    Marks artifacts as deleted without permanently removing them.
    Deleted artifacts can be restored using restore_artifacts.
    """)
)
class DeleteArtifactsInput:
    artifact_ids: list[ID]


@strawberry.input(
    description=dedent_strip("""
    Added in 25.15.0.

    Input for restoring previously deleted artifacts.

    Reverses the soft-delete operation, making the artifacts available again.
    """)
)
class RestoreArtifactsInput:
    artifact_ids: list[ID]


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Input for approving an artifact revision.

    Admin-only operation to approve artifact revisions for general use.
    """)
)
class ApproveArtifactInput:
    artifact_revision_id: ID


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Input for rejecting an artifact revision.

    Admin-only operation to reject artifact revisions, preventing their use.
    """)
)
class RejectArtifactInput:
    artifact_revision_id: ID


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Input for subscribing to artifact status change notifications.

    Used with artifact_status_changed subscription to receive real-time updates
    when artifact revision statuses change.
    """)
)
class ArtifactStatusChangedInput:
    artifact_revision_ids: list[ID]


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Specifies a target model for scanning operations.

    Used to identify specific models in external registries for detailed scanning.
    If revision is not specified, defaults to 'main' revision.
    """)
)
class ModelTarget:
    model_id: str
    revision: Optional[str] = None

    def to_dataclass(self) -> ModelTargetData:
        return ModelTargetData(model_id=self.model_id, revision=self.revision)


@strawberry.input(
    description=dedent_strip("""
    Added in 25.14.0.

    Input for batch scanning of specific models from external registries.

    Scans multiple specified models and retrieves detailed information including
    README content and file sizes. This operation performs immediate detailed scanning
    unlike the general scan_artifacts which only retrieves basic metadata.
    """)
)
class ScanArtifactModelsInput:
    models: list[ModelTarget]
    registry_id: Optional[uuid.UUID] = None


# Object Types
@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Information about the source or registry of an artifact.

    Contains the name and URL of the registry where the artifact is stored or originates from.
    """)
)
class SourceInfo:
    name: Optional[str]
    url: Optional[str]


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    An artifact represents AI models, packages, images, or other resources that can be
    stored, managed, and used within Backend.AI.

    Artifacts are discovered through scanning external registries and,
    can have multiple revisions.

    Each artifact contains metadata and references to its source registry.

    Key concepts:
    - Type: MODEL, PACKAGE, or IMAGE
    - Availability: ALIVE (available), DELETED (soft-deleted)
    - Source: Original external registry where it was discovered
    """)
)
class Artifact(Node):
    id: NodeID[str]
    name: str
    type: ArtifactType
    description: Optional[str]
    registry: SourceInfo
    source: SourceInfo
    readonly: bool
    extra: Optional[JSON]
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

    @strawberry.field
    async def revisions(
        self,
        info: Info[StrawberryGQLContext],
        filter: Optional[ArtifactRevisionFilter] = None,
        order_by: Optional[list[ArtifactRevisionOrderBy]] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ArtifactRevisionConnection:
        from .fetcher import fetch_artifact_revisions

        if filter is None:
            filter = ArtifactRevisionFilter(artifact_id=ID(self.id))
        else:
            filter.artifact_id = ID(self.id)

        return await fetch_artifact_revisions(
            info,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
        )


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    A specific version/revision of an artifact containing the actual file data.

    Artifact revisions progress through different statuses:
    - SCANNED: Discovered in external registry, metadata only
    - PULLING: Currently downloading from external source
    - PULLED: Downloaded to temporary storage
    - AVAILABLE: Ready for use by users

    Contains version information, file size, README content, and timestamps.
    Most HuggingFace models only have a 'main' revision.
    """)
)
class ArtifactRevision(Node):
    id: NodeID[str]
    status: ArtifactStatus
    remote_status: Optional[ArtifactRemoteStatus] = strawberry.field(description="Added in 25.15.0")
    version: str
    readme: Optional[str]
    size: Optional[ByteSize]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    digest: Optional[str] = strawberry.field(
        description="Digest at the time of import. None for models that have not been imported. Added in 25.17.0"
    )
    verification_result: Optional[ArtifactVerificationGQLResult] = strawberry.field(
        description="Verification result containing malware scan results from all verifiers. None if not yet verified. Added in 25.17.0"
    )

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

        registry_meta_loader = DataLoader(
            apartial(ArtifactRegistryMeta.load_by_id, info.context),
        )

        registry_data = await registry_meta_loader.load(artifact_action_result.result.registry_id)
        source_registry_data = await registry_meta_loader.load(
            artifact_action_result.result.source_registry_id
        )

        return Artifact.from_dataclass(
            artifact_action_result.result, registry_data.url, source_registry_data.url
        )


ArtifactEdge = Edge[Artifact]
ArtifactRevisionEdge = Edge[ArtifactRevision]


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Paginated connection for artifacts with total count information.

    Used for relay-style pagination with cursor-based navigation.
    """)
)
class ArtifactConnection(Connection[Artifact]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Paginated connection for artifact revisions with total count information.

    Used for relay-style pagination with cursor-based navigation.
    """)
)
class ArtifactRevisionConnection(Connection[ArtifactRevision]):
    count: int

    def __init__(self, *args, count: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Payload for artifact import progress subscription events.

    Provides real-time updates during the artifact import process,
    including progress percentage and current status.
    """)
)
class ArtifactImportProgressUpdatedPayload:
    artifact_id: ID
    progress: float
    status: ArtifactStatus


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Response payload for artifact scanning operations.

    Contains the list of artifacts discovered during scanning of external registries.
    These artifacts are registered with SCANNED status and can be imported for actual use.
    """)
)
class ScanArtifactsPayload:
    artifacts: list[Artifact]


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Response payload for delegated artifact scanning operation.
    Contains the list of artifacts discovered during the scan of a reservoir registry's remote registry.
    These artifacts are now available for import or direct use.
""")
)
class DelegateScanArtifactsPayload:
    artifacts: list[Artifact] = strawberry.field(
        description="List of artifacts discovered during the delegated scan from the reservoir registry's remote registry"
    )


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Represents a background task for importing an artifact revision.

    Contains the task ID for monitoring progress and the associated artifact revision
    being imported from external registries.
    """)
)
class ArtifactRevisionImportTask:
    task_id: Optional[ID]
    artifact_revision: ArtifactRevision


# Mutation Payloads
@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Response payload for artifact import operations.

    Contains the imported artifact revisions and their associated background tasks.
    Tasks can be monitored to track the import progress from SCANNED to AVAILABLE status.
    """)
)
class ImportArtifactsPayload:
    artifact_revisions: ArtifactRevisionConnection
    tasks: list[ArtifactRevisionImportTask]


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Response payload for delegated artifact import operation.
    Contains the imported artifact revisions and associated background tasks.
    The tasks can be monitored to track the progress of the import operation.
""")
)
class DelegateImportArtifactsPayload:
    artifact_revisions: ArtifactRevisionConnection = strawberry.field(
        description="Connection of artifact revisions that were imported from the reservoir registry's remote registry"
    )
    tasks: list[ArtifactRevisionImportTask] = strawberry.field(
        description="List of background tasks created for importing the artifact revisions"
    )


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Response payload for artifact update operations.

    Returns the updated artifact with modified metadata properties.
    """)
)
class UpdateArtifactPayload:
    artifact: Artifact


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Response payload for artifact revision cleanup operations.

    Contains the cleaned artifact revisions that have had their stored data removed,
    transitioning them back to SCANNED status to free storage space.
    """)
)
class CleanupArtifactRevisionsPayload:
    artifact_revisions: ArtifactRevisionConnection


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Response payload for artifact revision approval operations.

    Contains the approved artifact revision. Admin-only operation.
    """)
)
class ApproveArtifactPayload:
    artifact_revision: ArtifactRevision


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Response payload for artifact revision rejection operations.

    Contains the rejected artifact revision. Admin-only operation.
    """)
)
class RejectArtifactPayload:
    artifact_revision: ArtifactRevision


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Response payload for canceling artifact import operations.

    Contains the artifact revision whose import was canceled,
    reverting its status back to SCANNED.
    """)
)
class CancelImportArtifactPayload:
    artifact_revision: ArtifactRevision


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Payload for artifact status change subscription events.

    Provides real-time notifications when artifact revision statuses change
    during import, cleanup, or other operations.
    """)
)
class ArtifactStatusChangedPayload:
    artifact_revision: ArtifactRevision


@strawberry.type(
    description=dedent_strip("""
    Added in 25.14.0.

    Response payload for batch model scanning operations.

    Contains the artifact revisions discovered during detailed scanning of specific models,
    including README content and file size information.
    """)
)
class ScanArtifactModelsPayload:
    artifact_revision: ArtifactRevisionConnection


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Response payload for artifact deletion operations.

    Contains the artifacts that were soft-deleted. These can be restored later.
    """)
)
class DeleteArtifactsPayload:
    artifacts: list[Artifact]


@strawberry.type(
    description=dedent_strip("""
    Added in 25.15.0.

    Response payload for artifact restoration operations.

    Contains the artifacts that were restored from soft-deleted state.
    """)
)
class RestoreArtifactsPayload:
    artifacts: list[Artifact]
