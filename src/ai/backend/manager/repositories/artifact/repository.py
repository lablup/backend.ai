import uuid
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from ai.backend.common.data.storage.registries.types import ModelData
from ai.backend.common.exception import (
    ArtifactAssociationDeletionError,
    ArtifactAssociationNotFoundError,
    ArtifactNotFoundError,
    ArtifactNotVerified,
    ArtifactRevisionNotFoundError,
    ArtifactUpdateError,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRegistryType,
    ArtifactRevisionData,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
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
)
from ai.backend.manager.repositories.types import (
    GenericQueryBuilder,
    PaginationOptions,
)

# Layer-specific decorator for artifact repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.ARTIFACT)


class ArtifactFilterApplier:
    """Applies artifact-specific filters to queries"""

    def apply_filters(self, stmt: Select, filters: ArtifactFilterOptions) -> Select:
        """Apply artifact filters to the query statement"""
        condition, stmt = self._build_filter_condition(stmt, filters)
        if condition is not None:
            stmt = stmt.where(condition)
        return stmt

    def _build_filter_condition(
        self, stmt: Select, filters: ArtifactFilterOptions
    ) -> tuple[Optional[Any], Select]:
        """Build a filter condition from ArtifactFilterOptions, handling logical operations"""
        conditions = []

        # Handle basic filters
        if filters.artifact_type is not None:
            conditions.append(ArtifactRow.type == filters.artifact_type)
        if filters.authorized is not None:
            conditions.append(ArtifactRow.authorized == filters.authorized)

        # Handle new StringFilter-based filters
        if filters.name_filter is not None:
            name_condition = filters.name_filter.apply_to_column(ArtifactRow.name)
            if name_condition is not None:
                conditions.append(name_condition)

        # Handle registry_filter by joining with registry tables

        # TODO: Handle to join with proper table?
        if filters.registry_filter is not None:
            from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow

            registry_condition = filters.registry_filter.apply_to_column(
                HuggingFaceRegistryRow.name
            )
            if registry_condition is not None:
                # Join with registry table and add condition
                stmt = stmt.join(
                    HuggingFaceRegistryRow,
                    HuggingFaceRegistryRow.id == ArtifactRow.registry_id,
                )
                conditions.append(registry_condition)

        # Handle source_filter by joining with source registry tables
        if filters.source_filter is not None:
            from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow

            source_registry = sa.orm.aliased(HuggingFaceRegistryRow)
            source_condition = filters.source_filter.apply_to_column(source_registry.name)
            if source_condition is not None:
                # Join with source registry table (using alias to avoid conflicts)
                stmt = stmt.join(
                    source_registry,
                    source_registry.id == ArtifactRow.source_registry_id,
                )
                conditions.append(source_condition)
        if filters.registry_id is not None:
            conditions.append(ArtifactRow.registry_id == filters.registry_id)
        if filters.registry_type is not None:
            conditions.append(ArtifactRow.registry_type == filters.registry_type)
        if filters.source_registry_id is not None:
            conditions.append(ArtifactRow.source_registry_id == filters.source_registry_id)
        if filters.source_registry_type is not None:
            conditions.append(ArtifactRow.source_registry_type == filters.source_registry_type)

        # Combine basic conditions with AND
        base_condition = None
        if conditions:
            base_condition = sa.and_(*conditions)

        # Handle logical operations
        logical_conditions = []

        # Handle AND operation
        if filters.AND is not None:
            and_condition, stmt = self._build_filter_condition(stmt, filters.AND)
            if and_condition is not None:
                logical_conditions.append(and_condition)

        # Handle OR operation
        if filters.OR is not None:
            or_condition, stmt = self._build_filter_condition(stmt, filters.OR)
            if or_condition is not None:
                if base_condition is not None:
                    # Combine base condition OR logical condition
                    base_condition = sa.or_(base_condition, or_condition)
                else:
                    base_condition = or_condition

        # Handle NOT operation
        if filters.NOT is not None:
            not_condition, stmt = self._build_filter_condition(stmt, filters.NOT)
            if not_condition is not None:
                logical_conditions.append(~not_condition)  # SQLAlchemy NOT operator

        # Combine all conditions
        all_conditions = []
        if base_condition is not None:
            all_conditions.append(base_condition)
        if logical_conditions:
            all_conditions.extend(logical_conditions)

        final_condition = None
        if all_conditions:
            if len(all_conditions) == 1:
                final_condition = all_conditions[0]
            else:
                final_condition = sa.and_(*all_conditions)

        return final_condition, stmt


class ArtifactOrderingApplier:
    """Applies artifact-specific ordering to queries"""

    def apply_ordering(
        self, stmt: Select, ordering: ArtifactOrderingOptions
    ) -> tuple[Select, list[tuple[sa.Column, bool]]]:
        """Apply artifact ordering to the query statement"""
        order_clauses = []
        sql_order_clauses = []

        for field, desc in ordering.order_by:
            order_column = getattr(ArtifactRow, field.value, ArtifactRow.name)
            order_clauses.append((order_column, desc))

            if desc:
                sql_order_clauses.append(order_column.desc())
            else:
                sql_order_clauses.append(order_column.asc())

        if sql_order_clauses:
            stmt = stmt.order_by(*sql_order_clauses)

        return stmt, order_clauses


class ArtifactModelConverter:
    """Converts ArtifactRow to ArtifactData"""

    def convert_to_data(self, model: ArtifactRow) -> ArtifactData:
        """Convert ArtifactRow instance to ArtifactData"""
        return model.to_dataclass()


class ArtifactRevisionFilterApplier:
    """Applies artifact revision-specific filters to queries"""

    def apply_filters(self, stmt: Select, filters: ArtifactRevisionFilterOptions) -> Select:
        """Apply artifact revision filters to the query statement"""
        condition, stmt = self._build_filter_condition(stmt, filters)
        if condition is not None:
            stmt = stmt.where(condition)
        return stmt

    def _build_filter_condition(
        self, stmt: Select, filters: ArtifactRevisionFilterOptions
    ) -> tuple[Optional[Any], Select]:
        """Build a filter condition from ArtifactRevisionFilterOptions, handling logical operations"""
        conditions = []

        # Handle basic filters
        if filters.artifact_id is not None:
            conditions.append(ArtifactRevisionRow.artifact_id == filters.artifact_id)
        if filters.status is not None:
            # Support multiple status values using IN clause
            status_values = [status.value for status in filters.status]
            conditions.append(ArtifactRevisionRow.status.in_(status_values))
        # Handle StringFilter-based version filter
        if filters.version_filter is not None:
            version_condition = filters.version_filter.apply_to_column(ArtifactRevisionRow.version)
            if version_condition is not None:
                conditions.append(version_condition)

        # Combine basic conditions with AND
        base_condition = None
        if conditions:
            base_condition = sa.and_(*conditions)

        # Handle logical operations
        logical_conditions = []

        # Handle AND operation
        if filters.AND is not None:
            and_condition, stmt = self._build_filter_condition(stmt, filters.AND)
            if and_condition is not None:
                logical_conditions.append(and_condition)

        # Handle OR operation
        if filters.OR is not None:
            or_condition, stmt = self._build_filter_condition(stmt, filters.OR)
            if or_condition is not None:
                if base_condition is not None:
                    # Combine base condition OR logical condition
                    base_condition = sa.or_(base_condition, or_condition)
                else:
                    base_condition = or_condition

        # Handle NOT operation
        if filters.NOT is not None:
            not_condition, stmt = self._build_filter_condition(stmt, filters.NOT)
            if not_condition is not None:
                logical_conditions.append(~not_condition)  # SQLAlchemy NOT operator

        # Combine all conditions
        all_conditions = []
        if base_condition is not None:
            all_conditions.append(base_condition)
        if logical_conditions:
            all_conditions.extend(logical_conditions)

        final_condition = None
        if all_conditions:
            if len(all_conditions) == 1:
                final_condition = all_conditions[0]
            else:
                final_condition = sa.and_(*all_conditions)

        return final_condition, stmt


class ArtifactRevisionOrderingApplier:
    """Applies artifact revision-specific ordering to queries"""

    def apply_ordering(
        self, stmt: Select, ordering: ArtifactRevisionOrderingOptions
    ) -> tuple[Select, list[tuple[sa.Column, bool]]]:
        """Apply artifact revision ordering to the query statement"""
        order_clauses = []
        sql_order_clauses = []

        for field, desc in ordering.order_by:
            order_column = getattr(
                ArtifactRevisionRow, field.value.lower(), ArtifactRevisionRow.created_at
            )
            order_clauses.append((order_column, desc))

            if desc:
                sql_order_clauses.append(order_column.desc())
            else:
                sql_order_clauses.append(order_column.asc())

        if sql_order_clauses:
            stmt = stmt.order_by(*sql_order_clauses)

        return stmt, order_clauses


class ArtifactRevisionModelConverter:
    """Converts ArtifactRevisionRow to ArtifactRevisionData"""

    def convert_to_data(self, model: ArtifactRevisionRow) -> ArtifactRevisionData:
        """Convert ArtifactRevisionRow instance to ArtifactRevisionData"""
        return model.to_dataclass()


class ArtifactRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

        # Initialize the generic paginator with artifact-specific components
        self._paginator = GenericQueryBuilder[
            ArtifactRow, ArtifactData, ArtifactFilterOptions, ArtifactOrderingOptions
        ](
            model_class=ArtifactRow,
            filter_applier=ArtifactFilterApplier(),
            ordering_applier=ArtifactOrderingApplier(),
            model_converter=ArtifactModelConverter(),
            cursor_type_name="Artifact",
        )

    @repository_decorator()
    async def get_artifact_by_id(self, artifact_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()
            return row.to_dataclass()

    @repository_decorator()
    async def get_artifact_revision_by_id(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.id == revision_id)
            )
            row: ArtifactRevisionRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError()
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
                raise ArtifactNotFoundError()
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
                raise ArtifactRevisionNotFoundError()
            return row.to_dataclass()

    @repository_decorator()
    async def list_artifact_revisions(self, artifact_id: uuid.UUID) -> list[ArtifactRevisionData]:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.artifact_id == artifact_id)
            )
            rows: list[ArtifactRevisionRow] = result.scalars().all()
            return [row.to_dataclass() for row in rows]

    @repository_decorator()
    async def upsert_huggingface_model_artifacts(
        self,
        model_list: list[ModelData],
        registry_id: uuid.UUID,
    ) -> list[ArtifactDataWithRevisions]:
        async with self._db.begin_session() as db_sess:
            # key: artifact_id
            artifacts_map: dict[uuid.UUID, tuple[ArtifactRow, list[ArtifactRevisionRow]]] = {}

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
                    )
                    db_sess.add(artifact_row)
                    await db_sess.flush()
                    await db_sess.refresh(artifact_row)

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
                    # Update existing revision
                    # TODO: Reset to SCANNED?
                    if model.modified_at:
                        existing_revision.updated_at = model.modified_at

                    # Check if version row already exists for this artifact
                    existing_version_stmt = sa.select(ArtifactVersionRow).where(
                        sa.and_(
                            ArtifactVersionRow.artifact_id == existing_artifact.id,
                            ArtifactVersionRow.version == model.revision,
                        )
                    )
                    existing_version_result = await db_sess.execute(existing_version_stmt)
                    existing_version = existing_version_result.scalar_one_or_none()

                    # Create version row if it doesn't exist
                    if existing_version is None:
                        artifact_version_row = ArtifactVersionRow(
                            artifact_id=existing_artifact.id, version=model.revision
                        )
                        db_sess.add(artifact_version_row)

                    await db_sess.flush()
                    await db_sess.refresh(existing_revision, attribute_names=["updated_at"])
                    artifacts_map[artifact_row.id][1].append(existing_revision)
                else:
                    # Insert new artifact revision
                    new_revision = ArtifactRevisionRow.from_huggingface_model_data(
                        artifact_id=artifact_row.id,
                        model_data=model,
                    )

                    db_sess.add(new_revision)
                    await db_sess.flush()
                    await db_sess.refresh(
                        new_revision, attribute_names=["id", "created_at", "updated_at"]
                    )
                    artifacts_map[artifact_row.id][1].append(new_revision)

            # Convert to ArtifactDataWithRevisions format
            result: list[ArtifactDataWithRevisions] = []
            for artifact_row, revision_rows in artifacts_map.values():
                artifact_data = artifact_row.to_dataclass()
                revision_data_list = [revision.to_dataclass() for revision in revision_rows]
                result.append(
                    ArtifactDataWithRevisions(artifact=artifact_data, revisions=revision_data_list)
                )

        return result

    @repository_decorator()
    async def associate_artifact_with_storage(
        self,
        artifact_id: uuid.UUID,
        storage_id: uuid.UUID,
    ) -> AssociationArtifactsStoragesData:
        async with self._db.begin_session() as db_sess:
            select_stmt = sa.select(AssociationArtifactsStorageRow.id).where(
                sa.and_(
                    AssociationArtifactsStorageRow.artifact_id == artifact_id,
                    AssociationArtifactsStorageRow.storage_id == storage_id,
                )
            )
            existing = (await db_sess.execute(select_stmt)).scalar_one_or_none()
            if existing is not None:
                return AssociationArtifactsStoragesData(
                    id=existing, artifact_id=artifact_id, storage_id=storage_id
                )

            insert_stmt = (
                sa.insert(AssociationArtifactsStorageRow)
                .values(artifact_id=artifact_id, storage_id=storage_id)
                .returning(AssociationArtifactsStorageRow.id)
            )

            result = await db_sess.execute(insert_stmt)
            existing = result.scalar_one_or_none()

            return AssociationArtifactsStoragesData(
                id=existing,
                artifact_id=artifact_id,
                storage_id=storage_id,
            )

    @repository_decorator()
    async def disassociate_artifact_with_storage(
        self, artifact_id: uuid.UUID, storage_id: uuid.UUID
    ) -> AssociationArtifactsStoragesData:
        async with self._db.begin_session() as db_sess:
            select_result = await db_sess.execute(
                sa.select(AssociationArtifactsStorageRow).where(
                    sa.and_(
                        AssociationArtifactsStorageRow.artifact_id == artifact_id,
                        AssociationArtifactsStorageRow.storage_id == storage_id,
                    )
                )
            )
            existing_row: AssociationArtifactsStorageRow = select_result.scalar_one_or_none()
            if existing_row is None:
                # TODO: Make exception
                raise ArtifactAssociationNotFoundError(
                    f"Association between artifact {artifact_id} and storage {storage_id} does not exist"
                )

            # Store the data before deletion
            association_data = AssociationArtifactsStoragesData(
                id=existing_row.id,
                artifact_id=existing_row.artifact_id,
                storage_id=existing_row.storage_id,
            )

            # Delete the association
            delete_result = await db_sess.execute(
                sa.delete(AssociationArtifactsStorageRow).where(
                    sa.and_(
                        AssociationArtifactsStorageRow.artifact_id == artifact_id,
                        AssociationArtifactsStorageRow.storage_id == storage_id,
                    )
                )
            )

            # TODO: Make exception
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

            if row.status != ArtifactStatus.NEEDS_APPROVAL:
                raise ArtifactNotVerified("Only verified artifacts could be approved")

            update_stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == revision_id)
                .values(status=ArtifactStatus.AVAILABLE.value)
                .returning(ArtifactRevisionRow)
            )

            result = await db_sess.execute(update_stmt)
            updated_row: ArtifactRevisionRow | None = result.scalar_one_or_none()

            if updated_row is None:
                raise ArtifactUpdateError()

            return updated_row.to_dataclass()

    @repository_decorator()
    async def disapprove_artifact(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.id == revision_id)
            )
            row: ArtifactRevisionRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError()

            if row.status != ArtifactStatus.AVAILABLE:
                raise ArtifactNotVerified("Only approved artifacts could be disapproved")

            update_stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == revision_id)
                .values(status=ArtifactStatus.NEEDS_APPROVAL.value)
                .returning(ArtifactRevisionRow)
            )

            result = await db_sess.execute(update_stmt)
            updated_row: ArtifactRevisionRow | None = result.scalar_one_or_none()

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
    async def update_artifact_revision_bytesize(
        self, artifact_revision_id: uuid.UUID, size: int
    ) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
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
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(readme=readme)
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

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

        # Build query using the generic paginator
        querybuild_result = self._paginator.build_pagination_queries(
            pagination=pagination or PaginationOptions(),
            ordering=ordering,
            filters=filters,
            select_options=[selectinload(ArtifactRow.revision_rows)],
        )

        async with self._db.begin_session() as db_sess:
            # Execute data query
            result = await db_sess.execute(querybuild_result.data_query)
            rows = result.scalars().all()

            count_stmt = sa.select(sa.func.count()).select_from(ArtifactRow)
            count_result = await db_sess.execute(count_stmt)
            total_count = count_result.scalar()

            # Convert to data objects using paginator
            data_objects = self._paginator.convert_rows_to_data(
                rows, querybuild_result.pagination_order
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
            if filters.status is not None:
                status_values = [status.value for status in filters.status]
                count_stmt = count_stmt.where(ArtifactRevisionRow.status.in_(status_values))
            if filters.version_filter is not None:
                version_condition = filters.version_filter.apply_to_column(
                    ArtifactRevisionRow.version
                )
                if version_condition is not None:
                    count_stmt = count_stmt.where(version_condition)

            count_result = await db_sess.execute(count_stmt)
            total_count = count_result.scalar()

            # Convert to data objects using paginator
            data_objects = revision_paginator.convert_rows_to_data(
                rows, querybuild_result.pagination_order
            )
            return data_objects, total_count
