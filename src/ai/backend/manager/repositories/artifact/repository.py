import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from datetime import datetime, timezone
from typing import Any, Optional, override

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload, sessionmaker
from sqlalchemy.sql import Select

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelData
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.artifact.modifier import ArtifactModifier
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRevisionData,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.errors.artifact import (
    ArtifactAssociationDeletionError,
    ArtifactAssociationNotFoundError,
    ArtifactNotFoundError,
    ArtifactNotVerified,
    ArtifactRevisionNotFoundError,
    ArtifactUpdateError,
    InvalidArtifactModifierTypeError,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.types import (
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
    ArtifactRevisionFilterOptions,
    ArtifactRevisionOrderingOptions,
    ArtifactStatusFilterType,
)
from ai.backend.manager.repositories.types import (
    BaseFilterApplier,
    BaseOrderingApplier,
    GenericQueryBuilder,
    PaginationOptions,
)

# Layer-specific decorator for artifact repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.ARTIFACT)


class ArtifactFilterApplier(BaseFilterApplier[ArtifactFilterOptions]):
    """Applies artifact-specific filters to queries"""

    @override
    def apply_entity_filters(
        self, stmt: Select, filters: ArtifactFilterOptions
    ) -> tuple[list[Any], Select]:
        """Apply artifact-specific filters and return list of conditions and updated statement"""
        conditions = []

        # Handle basic filters
        if filters.artifact_type:
            conditions.append(ArtifactRow.type.in_(filters.artifact_type))

        # Handle StringFilter-based filters
        if filters.name_filter is not None:
            name_condition = filters.name_filter.apply_to_column(ArtifactRow.name)
            if name_condition is not None:
                conditions.append(name_condition)

        # Handle registry_filter by joining with registry tables
        if filters.registry_filter is not None:
            from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow

            registry_condition = filters.registry_filter.apply_to_column(ArtifactRegistryRow.name)
            if registry_condition is not None:
                # Join with artifact registry table and add condition
                stmt = stmt.join(
                    ArtifactRegistryRow,
                    ArtifactRegistryRow.registry_id == ArtifactRow.registry_id,
                )
                conditions.append(registry_condition)

        # Handle source_filter by joining with source registry tables
        if filters.source_filter is not None:
            from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow

            source_registry = sa.orm.aliased(ArtifactRegistryRow)
            source_condition = filters.source_filter.apply_to_column(source_registry.name)
            if source_condition is not None:
                # Join with source registry table (using alias to avoid conflicts)
                stmt = stmt.join(
                    source_registry,
                    source_registry.registry_id == ArtifactRow.source_registry_id,
                )
                conditions.append(source_condition)

        # Handle ID and type filters
        if filters.registry_id is not None:
            conditions.append(ArtifactRow.registry_id == filters.registry_id)
        if filters.registry_type is not None:
            conditions.append(ArtifactRow.registry_type == filters.registry_type)
        if filters.source_registry_id is not None:
            conditions.append(ArtifactRow.source_registry_id == filters.source_registry_id)
        if filters.source_registry_type is not None:
            conditions.append(ArtifactRow.source_registry_type == filters.source_registry_type)

        # Handle availability filter
        if filters.availability:
            conditions.append(ArtifactRow.availability.in_(filters.availability))

        return conditions, stmt


class ArtifactOrderingApplier(BaseOrderingApplier[ArtifactOrderingOptions]):
    """Applies artifact-specific ordering to queries"""

    @override
    def get_order_column(self, field) -> sa.Column:
        """Get the SQLAlchemy column for the given artifact field"""
        return getattr(ArtifactRow, field.value.lower(), ArtifactRow.name)


class ArtifactModelConverter:
    """Converts ArtifactRow to ArtifactData"""

    def convert_to_data(self, model: ArtifactRow) -> ArtifactData:
        """Convert ArtifactRow instance to ArtifactData"""
        return model.to_dataclass()


class ArtifactRevisionFilterApplier(BaseFilterApplier[ArtifactRevisionFilterOptions]):
    """Applies artifact revision-specific filters to queries"""

    @override
    def apply_entity_filters(
        self, stmt: Select, filters: ArtifactRevisionFilterOptions
    ) -> tuple[list[Any], Select]:
        """Apply artifact revision-specific filters and return list of conditions and updated statement"""
        conditions = []

        # Handle basic filters
        if filters.artifact_id is not None:
            conditions.append(ArtifactRevisionRow.artifact_id == filters.artifact_id)
        if filters.status_filter is not None:
            # Handle different status filter types
            status_values = [status.value for status in filters.status_filter.values]
            if filters.status_filter.type == ArtifactStatusFilterType.IN:
                conditions.append(ArtifactRevisionRow.status.in_(status_values))
            elif filters.status_filter.type == ArtifactStatusFilterType.EQUALS:
                conditions.append(ArtifactRevisionRow.status == status_values[0])

        # Handle StringFilter-based version filter
        if filters.version_filter is not None:
            version_condition = filters.version_filter.apply_to_column(ArtifactRevisionRow.version)
            if version_condition is not None:
                conditions.append(version_condition)

        # Handle IntFilter-based size filter
        if filters.size_filter is not None:
            size_condition = filters.size_filter.apply_to_column(ArtifactRevisionRow.size)
            if size_condition is not None:
                conditions.append(size_condition)

        return conditions, stmt


class ArtifactRevisionOrderingApplier(BaseOrderingApplier[ArtifactRevisionOrderingOptions]):
    """Applies artifact revision-specific ordering to queries"""

    @override
    def get_order_column(self, field) -> sa.Column:
        """Get the SQLAlchemy column for the given artifact revision field"""
        return getattr(ArtifactRevisionRow, field.value.lower(), ArtifactRevisionRow.created_at)


class ArtifactRevisionModelConverter:
    """Converts ArtifactRevisionRow to ArtifactRevisionData"""

    def convert_to_data(self, model: ArtifactRevisionRow) -> ArtifactRevisionData:
        """Convert ArtifactRevisionRow instance to ArtifactRevisionData"""
        return model.to_dataclass()


class ArtifactRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_artifact_by_id(self, artifact_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def get_artifact_revision_by_id(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.id == revision_id)
            )
            row: ArtifactRevisionRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError(
                    f"Artifact revision with ID {revision_id} not found"
                )
            return row.to_dataclass()

    @repository_decorator()
    async def get_model_artifact(self, model_id: str, registry_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(
                    sa.and_(ArtifactRow.name == model_id, ArtifactRow.registry_id == registry_id)
                )
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(
                    f"Artifact with model ID {model_id} not found under registry {registry_id}"
                )
            return row.to_dataclass()

    @repository_decorator()
    async def get_artifact_revision(
        self, artifact_id: uuid.UUID, revision: str
    ) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(
                    sa.and_(
                        ArtifactRevisionRow.artifact_id == artifact_id,
                        ArtifactRevisionRow.version == revision,
                    )
                )
            )
            row: ArtifactRevisionRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError(f"Revision {revision} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def update_artifact(
        self, artifact_id: uuid.UUID, modifier: ArtifactModifier
    ) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            data = modifier.fields_to_update()
            if not data:
                raise InvalidArtifactModifierTypeError("No valid fields to update")

            result = await db_sess.execute(
                sa.update(ArtifactRow)
                .where(
                    sa.and_(
                        ArtifactRow.id == artifact_id,
                        ArtifactRow.availability != ArtifactAvailability.DELETED,
                    )
                )
                .values(**data)
            )
            if result.rowcount == 0:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            await db_sess.commit()

            result = await db_sess.execute(
                sa.select(ArtifactRow).where(
                    sa.and_(
                        ArtifactRow.id == artifact_id,
                        ArtifactRow.availability != ArtifactAvailability.DELETED,
                    )
                )
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            return row.to_dataclass()

    @repository_decorator()
    async def list_artifact_revisions(self, artifact_id: uuid.UUID) -> list[ArtifactRevisionData]:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.artifact_id == artifact_id)
            )
            rows: list[ArtifactRevisionRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    # TODO: Refactor using on_conflict_do_update?
    @repository_decorator()
    async def upsert_artifacts(
        self,
        artifacts: list[ArtifactData],
    ) -> list[ArtifactData]:
        async with self._db.begin_session() as db_sess:
            result_artifacts: list[ArtifactData] = []

            for artifact_data in artifacts:
                # Check if artifact exists
                artifact_query_result = await db_sess.execute(
                    sa.select(ArtifactRow).where(
                        sa.and_(
                            ArtifactRow.name == artifact_data.name,
                            ArtifactRow.registry_id == artifact_data.registry_id,
                        )
                    )
                )
                existing_artifact: ArtifactRow = artifact_query_result.scalar_one_or_none()

                if existing_artifact is None:
                    # Create new artifact
                    new_artifact = ArtifactRow(
                        id=artifact_data.id,
                        name=artifact_data.name,
                        type=artifact_data.type,
                        description=artifact_data.description,
                        registry_id=artifact_data.registry_id,
                        source_registry_id=artifact_data.source_registry_id,
                        registry_type=artifact_data.registry_type,
                        source_registry_type=artifact_data.source_registry_type,
                        readonly=True,  # always overwrite readonly to True
                    )
                    db_sess.add(new_artifact)
                    await db_sess.flush()
                    await db_sess.refresh(
                        new_artifact, attribute_names=["scanned_at", "updated_at"]
                    )
                    result_artifacts.append(new_artifact.to_dataclass())
                else:
                    # Update existing artifact
                    has_changes = existing_artifact.description != artifact_data.description
                    if has_changes:
                        existing_artifact.description = artifact_data.description
                        existing_artifact.updated_at = datetime.now(timezone.utc)

                    await db_sess.flush()
                    await db_sess.refresh(
                        existing_artifact, attribute_names=["scanned_at", "updated_at"]
                    )
                    result_artifacts.append(existing_artifact.to_dataclass())

            return result_artifacts

    @repository_decorator()
    async def upsert_artifact_revisions(
        self,
        revisions: list[ArtifactRevisionData],
    ) -> list[ArtifactRevisionData]:
        async with self._db.begin_session() as db_sess:
            result_revisions: list[ArtifactRevisionData] = []
            artifact_ids_to_update: set[uuid.UUID] = set()

            for revision_data in revisions:
                # Skip failed or rejected revision copy
                if revision_data.status in [ArtifactStatus.FAILED, ArtifactStatus.REJECTED]:
                    continue

                # Check if revision exists
                revision_query_result = await db_sess.execute(
                    sa.select(ArtifactRevisionRow).where(
                        sa.and_(
                            ArtifactRevisionRow.artifact_id == revision_data.artifact_id,
                            ArtifactRevisionRow.version == revision_data.version,
                        )
                    )
                )
                existing_revision: ArtifactRevisionRow = revision_query_result.scalar_one_or_none()

                if existing_revision is None:
                    # Create new revision
                    new_revision = ArtifactRevisionRow(
                        id=revision_data.id,
                        artifact_id=revision_data.artifact_id,
                        version=revision_data.version,
                        readme=revision_data.readme,
                        size=revision_data.size,
                        status=ArtifactStatus.SCANNED,
                        remote_status=revision_data.remote_status,
                        created_at=revision_data.created_at,
                        updated_at=revision_data.updated_at,
                    )
                    db_sess.add(new_revision)
                    await db_sess.flush()
                    await db_sess.refresh(new_revision)
                    result_revisions.append(new_revision.to_dataclass())
                    artifact_ids_to_update.add(revision_data.artifact_id)
                else:
                    # Update existing revision only if there are changes
                    has_changes = (
                        existing_revision.readme != revision_data.readme
                        or existing_revision.size != revision_data.size
                        or existing_revision.created_at != revision_data.created_at
                        or existing_revision.updated_at != revision_data.updated_at
                    )

                    if has_changes:
                        existing_revision.readme = revision_data.readme
                        existing_revision.size = revision_data.size
                        existing_revision.created_at = revision_data.created_at
                        existing_revision.updated_at = revision_data.updated_at
                        existing_revision.remote_status = revision_data.remote_status
                        artifact_ids_to_update.add(revision_data.artifact_id)

                    await db_sess.flush()
                    await db_sess.refresh(existing_revision)
                    result_revisions.append(existing_revision.to_dataclass())

            # Update artifact updated_at timestamp for affected artifacts
            if artifact_ids_to_update:
                await db_sess.execute(
                    sa.update(ArtifactRow)
                    .where(ArtifactRow.id.in_(artifact_ids_to_update))
                    .values(updated_at=sa.func.now())
                )

            return result_revisions

    @repository_decorator()
    async def upsert_huggingface_model_artifacts(
        self,
        model_list: list[ModelData],
        registry_id: uuid.UUID,
    ) -> list[ArtifactDataWithRevisions]:
        async with self._db.begin_session() as db_sess:
            # key: artifact_id
            artifacts_map: dict[uuid.UUID, tuple[ArtifactRow, list[ArtifactRevisionRow]]] = {}
            artifact_ids_to_update: set[uuid.UUID] = set()

            for model in model_list:
                # Check if artifact exists within the current session
                artifact_query_result = await db_sess.execute(
                    sa.select(ArtifactRow).where(
                        sa.and_(
                            ArtifactRow.name == model.id, ArtifactRow.registry_id == registry_id
                        )
                    )
                )
                artifact_row: ArtifactRow = artifact_query_result.scalar_one_or_none()

                if artifact_row is None:
                    # Create new artifact
                    artifact_row = ArtifactRow(
                        type=ArtifactType.MODEL,
                        name=model.id,
                        registry_id=registry_id,
                        registry_type=ArtifactRegistryType.HUGGINGFACE,
                        source_registry_id=registry_id,
                        source_registry_type=ArtifactRegistryType.HUGGINGFACE,
                        readonly=True,
                    )
                    db_sess.add(artifact_row)
                    await db_sess.flush()
                    await db_sess.refresh(
                        artifact_row, attribute_names=["scanned_at", "updated_at"]
                    )

                # Initialize artifact in map if not exists
                if artifact_row.id not in artifacts_map:
                    artifacts_map[artifact_row.id] = (artifact_row, [])

                # Check if artifact revision exists
                revision_query_result = await db_sess.execute(
                    sa.select(ArtifactRevisionRow).where(
                        sa.and_(
                            ArtifactRevisionRow.artifact_id == artifact_row.id,
                            ArtifactRevisionRow.version == model.revision,
                        )
                    )
                )

                existing_revision: ArtifactRevisionRow = revision_query_result.scalar_one_or_none()
                if existing_revision is not None:
                    # Update existing revision only if there are changes
                    has_changes = (
                        existing_revision.readme != model.readme
                        or existing_revision.updated_at != model.modified_at
                        or existing_revision.created_at != model.created_at
                    )

                    if has_changes:
                        existing_revision.readme = model.readme
                        existing_revision.updated_at = model.modified_at
                        artifact_ids_to_update.add(artifact_row.id)

                    await db_sess.flush()
                    await db_sess.refresh(existing_revision)
                    artifacts_map[artifact_row.id][1].append(existing_revision)
                else:
                    # Insert new artifact revision
                    new_revision = ArtifactRevisionRow.from_huggingface_model_data(
                        artifact_id=artifact_row.id,
                        model_data=model,
                    )

                    db_sess.add(new_revision)
                    await db_sess.flush()
                    await db_sess.refresh(new_revision)
                    artifacts_map[artifact_row.id][1].append(new_revision)
                    artifact_ids_to_update.add(artifact_row.id)

            # Update artifact updated_at timestamp for affected artifacts
            if artifact_ids_to_update:
                await db_sess.execute(
                    sa.update(ArtifactRow)
                    .where(ArtifactRow.id.in_(artifact_ids_to_update))
                    .values(updated_at=sa.func.now())
                )

                # Refresh updated_at for affected artifacts
                for artifact_id, (artifact_row, _revs) in artifacts_map.items():
                    if artifact_id in artifact_ids_to_update:
                        await db_sess.refresh(artifact_row, attribute_names=["updated_at"])

            # Convert to ArtifactDataWithRevisions format
            result: list[ArtifactDataWithRevisions] = []
            for artifact_row, revision_rows in artifacts_map.values():
                artifact_data = artifact_row.to_dataclass()
                revision_data_list = [revision.to_dataclass() for revision in revision_rows]
                result.append(
                    ArtifactDataWithRevisions.from_dataclasses(
                        artifact_data=artifact_data, revisions=revision_data_list
                    )
                )

        return result

    @repository_decorator()
    async def associate_artifact_with_storage(
        self,
        artifact_revision_id: uuid.UUID,
        storage_namespace_id: uuid.UUID,
        storage_type: ArtifactStorageType,
    ) -> AssociationArtifactsStoragesData:
        async with self._db.begin_session() as db_sess:
            select_stmt = sa.select(AssociationArtifactsStorageRow.id).where(
                sa.and_(
                    AssociationArtifactsStorageRow.artifact_revision_id == artifact_revision_id,
                    AssociationArtifactsStorageRow.storage_namespace_id == storage_namespace_id,
                )
            )
            existing = (await db_sess.execute(select_stmt)).scalar_one_or_none()
            if existing is not None:
                return AssociationArtifactsStoragesData(
                    id=existing,
                    artifact_revision_id=artifact_revision_id,
                    storage_namespace_id=storage_namespace_id,
                )

            insert_stmt = (
                sa.insert(AssociationArtifactsStorageRow)
                .values(
                    artifact_revision_id=artifact_revision_id,
                    storage_namespace_id=storage_namespace_id,
                    storage_type=storage_type.value,
                )
                .returning(AssociationArtifactsStorageRow.id)
            )

            result = await db_sess.execute(insert_stmt)
            existing = result.scalar_one_or_none()

            return AssociationArtifactsStoragesData(
                id=existing,
                artifact_revision_id=artifact_revision_id,
                storage_namespace_id=storage_namespace_id,
            )

    @repository_decorator()
    async def disassociate_artifact_with_storage(
        self, artifact_revision_id: uuid.UUID, storage_namespace_id: uuid.UUID
    ) -> AssociationArtifactsStoragesData:
        async with self._db.begin_session() as db_sess:
            select_result = await db_sess.execute(
                sa.select(AssociationArtifactsStorageRow).where(
                    sa.and_(
                        AssociationArtifactsStorageRow.artifact_revision_id == artifact_revision_id,
                        AssociationArtifactsStorageRow.storage_namespace_id == storage_namespace_id,
                    )
                )
            )
            existing_row: AssociationArtifactsStorageRow = select_result.scalar_one_or_none()
            if existing_row is None:
                raise ArtifactAssociationNotFoundError(
                    f"Association between artifact {artifact_revision_id} and storage {storage_namespace_id} does not exist"
                )

            # Store the data before deletion
            association_data = AssociationArtifactsStoragesData(
                id=existing_row.id,
                artifact_revision_id=existing_row.artifact_revision_id,
                storage_namespace_id=existing_row.storage_namespace_id,
            )

            # Delete the association
            delete_result = await db_sess.execute(
                sa.delete(AssociationArtifactsStorageRow).where(
                    sa.and_(
                        AssociationArtifactsStorageRow.artifact_revision_id == artifact_revision_id,
                        AssociationArtifactsStorageRow.storage_namespace_id == storage_namespace_id,
                    )
                )
            )

            if delete_result.rowcount == 0:
                raise ArtifactAssociationDeletionError("Failed to delete association")

            return association_data

    @repository_decorator()
    async def approve_artifact(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.id == revision_id)
            )
            row: ArtifactRevisionRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError()

            if row.status == ArtifactStatus.AVAILABLE:
                raise ArtifactNotVerified("Artifacts already approved")
            if row.status != ArtifactStatus.NEEDS_APPROVAL:
                raise ArtifactNotVerified("Only verified artifacts could be approved")

            update_stmt = (
                sa.update(ArtifactRevisionRow)
                .where(
                    sa.and_(
                        ArtifactRevisionRow.id == revision_id,
                        ArtifactRevisionRow.status == ArtifactStatus.NEEDS_APPROVAL,
                    )
                )
                .values(status=ArtifactStatus.AVAILABLE)
                .returning(ArtifactRevisionRow)
            )

            result = await db_sess.execute(update_stmt)
            updated_id = result.scalar_one_or_none()
            if updated_id is None:
                raise ArtifactUpdateError()

            updated_row = await db_sess.get(ArtifactRevisionRow, updated_id)
            if updated_row is None:
                raise ArtifactUpdateError()

            return updated_row.to_dataclass()

    @repository_decorator()
    async def reject_artifact(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.id == revision_id)
            )
            row: ArtifactRevisionRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError()

            update_stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == revision_id)
                .values(status=ArtifactStatus.REJECTED.value)
                .returning(ArtifactRevisionRow)
            )

            result = await db_sess.execute(update_stmt)
            updated_id = result.scalar_one_or_none()
            if updated_id is None:
                raise ArtifactUpdateError()

            updated_row = await db_sess.get(ArtifactRevisionRow, updated_id)
            if updated_row is None:
                raise ArtifactUpdateError()

            return updated_row.to_dataclass()

    @repository_decorator()
    async def reset_artifact_revision_status(self, revision_id: uuid.UUID) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == revision_id)
                .values(status=ArtifactStatus.SCANNED)
            )
            await db_sess.execute(stmt)
            return revision_id

    @repository_decorator()
    async def update_artifact_revision_status(
        self, artifact_revision_id: uuid.UUID, status: ArtifactStatus
    ) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(status=status)
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

    @repository_decorator()
    async def delete_artifacts(self, artifact_ids: list[uuid.UUID]) -> list[ArtifactData]:
        async with self._db.begin_session() as db_sess:
            # Update availability to DELETED for the given artifact IDs (only for ALIVE artifacts)
            await db_sess.execute(
                sa.update(ArtifactRow)
                .where(
                    sa.and_(
                        ArtifactRow.id.in_(artifact_ids),
                        ArtifactRow.availability != ArtifactAvailability.DELETED,
                    )
                )
                .values(availability=ArtifactAvailability.DELETED.value)
            )

            # Fetch and return the updated artifacts
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id.in_(artifact_ids))
            )
            rows: list[ArtifactRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @repository_decorator()
    async def restore_artifacts(self, artifact_ids: list[uuid.UUID]) -> list[ArtifactData]:
        async with self._db.begin_session() as db_sess:
            # Update availability to ALIVE for the given artifact IDs (only for DELETED artifacts)
            await db_sess.execute(
                sa.update(ArtifactRow)
                .where(
                    sa.and_(
                        ArtifactRow.id.in_(artifact_ids),
                        ArtifactRow.availability == ArtifactAvailability.DELETED,
                    )
                )
                .values(availability=ArtifactAvailability.ALIVE.value)
            )

            # Fetch and return the updated artifacts
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id.in_(artifact_ids))
            )
            rows: list[ArtifactRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @repository_decorator()
    async def update_artifact_revision_bytesize(
        self, artifact_revision_id: uuid.UUID, size: int
    ) -> uuid.UUID:
        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(size=size)
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

    @repository_decorator()
    async def update_artifact_revision_readme(
        self, artifact_revision_id: uuid.UUID, readme: str
    ) -> uuid.UUID:
        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(readme=readme)
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

    @repository_decorator()
    async def get_artifact_revision_readme(self, artifact_revision_id: uuid.UUID) -> str:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow.readme).where(
                    ArtifactRevisionRow.id == artifact_revision_id
                )
            )
            readme = result.scalar_one_or_none()
            return readme

    @repository_decorator()
    async def list_artifacts_paginated(
        self,
        *,
        pagination: Optional[PaginationOptions] = None,
        ordering: Optional[ArtifactOrderingOptions] = None,
        filters: Optional[ArtifactFilterOptions] = None,
    ) -> tuple[list[ArtifactData], int]:
        """List artifacts with pagination and filtering.

        Args:
            pagination: Pagination options for the query
            ordering: Ordering options for the query
            filters: Filtering options for artifacts

        Returns:
            Tuple of (artifacts list, total count)
        """
        # Set defaults
        if ordering is None:
            ordering = ArtifactOrderingOptions()
        if filters is None:
            filters = ArtifactFilterOptions()

        # Initialize the generic paginator with artifact-specific components
        artifact_paginator = GenericQueryBuilder[
            ArtifactRow, ArtifactData, ArtifactFilterOptions, ArtifactOrderingOptions
        ](
            model_class=ArtifactRow,
            filter_applier=ArtifactFilterApplier(),
            ordering_applier=ArtifactOrderingApplier(),
            model_converter=ArtifactModelConverter(),
            cursor_type_name="Artifact",
        )

        # Build query using the generic paginator
        querybuild_result = artifact_paginator.build_pagination_queries(
            pagination=pagination or PaginationOptions(),
            ordering=ordering,
            filters=filters,
            select_options=[selectinload(ArtifactRow.revision_rows)],
        )

        async with self._db.begin_session() as db_sess:
            # Execute data query
            result = await db_sess.execute(querybuild_result.data_query)
            rows = result.scalars().all()

            # Build count query with same filters applied
            count_stmt = sa.select(sa.func.count()).select_from(ArtifactRow)
            if filters is not None:
                count_stmt = artifact_paginator.filter_applier.apply_filters(count_stmt, filters)
            count_result = await db_sess.execute(count_stmt)
            total_count = count_result.scalar()

            # Convert to data objects using paginator
            data_objects = artifact_paginator.convert_rows_to_data(
                rows, querybuild_result.pagination_order
            )
            return data_objects, total_count

    @repository_decorator()
    async def list_artifacts_with_revisions_paginated(
        self,
        *,
        pagination: Optional[PaginationOptions] = None,
        ordering: Optional[ArtifactOrderingOptions] = None,
        filters: Optional[ArtifactFilterOptions] = None,
    ) -> tuple[list[ArtifactDataWithRevisions], int]:
        """List artifacts with their revisions using pagination and filtering.

        Args:
            pagination: Pagination options for the query
            ordering: Ordering options for the query
            filters: Filtering options for artifacts

        Returns:
            Tuple of (artifacts with revisions list, total count)
        """
        # Set defaults
        if ordering is None:
            ordering = ArtifactOrderingOptions()
        if filters is None:
            filters = ArtifactFilterOptions()

        # Initialize the generic paginator with artifact-specific components
        artifact_paginator = GenericQueryBuilder[
            ArtifactRow, ArtifactData, ArtifactFilterOptions, ArtifactOrderingOptions
        ](
            model_class=ArtifactRow,
            filter_applier=ArtifactFilterApplier(),
            ordering_applier=ArtifactOrderingApplier(),
            model_converter=ArtifactModelConverter(),
            cursor_type_name="Artifact",
        )

        # Build query using the generic paginator with eager loading of revisions
        querybuild_result = artifact_paginator.build_pagination_queries(
            pagination=pagination or PaginationOptions(),
            ordering=ordering,
            filters=filters,
            select_options=[selectinload(ArtifactRow.revision_rows)],
        )

        async with self._db.begin_session() as db_sess:
            # Execute data query
            result = await db_sess.execute(querybuild_result.data_query)
            rows = result.scalars().all()

            # Build count query with same filters applied
            count_stmt = sa.select(sa.func.count()).select_from(ArtifactRow)
            if filters is not None:
                count_stmt = artifact_paginator.filter_applier.apply_filters(count_stmt, filters)
            count_result = await db_sess.execute(count_stmt)
            total_count = count_result.scalar()

            # Convert to ArtifactDataWithRevisions objects
            data_objects: list[ArtifactDataWithRevisions] = []
            for row in rows:
                artifact_data = row.to_dataclass()
                revisions_data = [revision.to_dataclass() for revision in row.revision_rows]
                data_objects.append(
                    ArtifactDataWithRevisions.from_dataclasses(
                        artifact_data=artifact_data, revisions=revisions_data
                    )
                )

            return data_objects, total_count

    @repository_decorator()
    async def list_artifact_revisions_paginated(
        self,
        *,
        pagination: Optional[PaginationOptions] = None,
        ordering: Optional[ArtifactRevisionOrderingOptions] = None,
        filters: Optional[ArtifactRevisionFilterOptions] = None,
    ) -> tuple[list[ArtifactRevisionData], int]:
        """List artifact revisions with pagination and filtering.

        Args:
            pagination: Pagination options for the query
            ordering: Ordering options for the query
            filters: Filtering options for artifact revisions

        Returns:
            Tuple of (artifact revisions list, total count)
        """
        # Set defaults
        if ordering is None:
            ordering = ArtifactRevisionOrderingOptions()
        if filters is None:
            filters = ArtifactRevisionFilterOptions()

        # Create a generic query builder for ArtifactRevision
        revision_paginator = GenericQueryBuilder[
            ArtifactRevisionRow,
            ArtifactRevisionData,
            ArtifactRevisionFilterOptions,
            ArtifactRevisionOrderingOptions,
        ](
            model_class=ArtifactRevisionRow,
            filter_applier=ArtifactRevisionFilterApplier(),
            ordering_applier=ArtifactRevisionOrderingApplier(),
            model_converter=ArtifactRevisionModelConverter(),
            cursor_type_name="ArtifactRevision",
        )

        # Build query using the generic paginator
        querybuild_result = revision_paginator.build_pagination_queries(
            pagination=pagination or PaginationOptions(),
            ordering=ordering,
            filters=filters,
        )

        async with self._db.begin_session() as db_sess:
            # Execute data query
            result = await db_sess.execute(querybuild_result.data_query)
            rows = result.scalars().all()

            # Build count query with same filters
            count_stmt = sa.select(sa.func.count()).select_from(ArtifactRevisionRow)
            if filters.artifact_id is not None:
                count_stmt = count_stmt.where(
                    ArtifactRevisionRow.artifact_id == filters.artifact_id
                )
            if filters.status_filter is not None:
                status_values = [status.value for status in filters.status_filter.values]
                if filters.status_filter.type == ArtifactStatusFilterType.IN:
                    count_stmt = count_stmt.where(ArtifactRevisionRow.status.in_(status_values))
                elif filters.status_filter.type == ArtifactStatusFilterType.EQUALS:
                    count_stmt = count_stmt.where(ArtifactRevisionRow.status == status_values[0])
            if filters.version_filter is not None:
                version_condition = filters.version_filter.apply_to_column(
                    ArtifactRevisionRow.version
                )
                if version_condition is not None:
                    count_stmt = count_stmt.where(version_condition)
            if filters.size_filter is not None:
                size_condition = filters.size_filter.apply_to_column(ArtifactRevisionRow.size)
                if size_condition is not None:
                    count_stmt = count_stmt.where(size_condition)

            count_result = await db_sess.execute(count_stmt)
            total_count = count_result.scalar()

            # Convert to data objects using paginator
            data_objects = revision_paginator.convert_rows_to_data(
                rows, querybuild_result.pagination_order
            )
            return data_objects, total_count

    @actxmgr
    async def _begin_session_read_committed(self) -> AsyncIterator[SASession]:
        """
        Begin a read-write session with READ COMMITTED isolation level.
        """
        async with self._db.connect() as conn:
            # Set isolation level to READ COMMITTED
            conn_with_isolation = await conn.execution_options(isolation_level="READ COMMITTED")
            async with conn_with_isolation.begin():
                # Configure session factory with the connection
                sess_factory = sessionmaker(
                    bind=conn_with_isolation,
                    class_=SASession,
                    expire_on_commit=False,
                )
                session = sess_factory()
                yield session
                await session.commit()
