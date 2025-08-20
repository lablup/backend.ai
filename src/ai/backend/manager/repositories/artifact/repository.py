import uuid
from typing import Any, Generic, Optional, Protocol, TypeVar

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
)
from ai.backend.manager.repositories.types import (
    PaginationOptions,
)

# Layer-specific decorator for artifact repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.ARTIFACT)

# Generic types for pagination
TModel = TypeVar("TModel")
TData = TypeVar("TData")
TFilters = TypeVar("TFilters")
TOrdering = TypeVar("TOrdering")


class PaginatableModel(Protocol):
    """Protocol for models that can be paginated"""

    id: Any


class FilterApplier(Protocol):
    """Protocol for applying filters to a query"""

    def apply_filters(self, stmt: Select, filters: Any) -> Select:
        """Apply filters to the query statement"""
        ...


class OrderingApplier(Protocol):
    """Protocol for applying ordering to a query"""

    def apply_ordering(
        self, stmt: Select, ordering: Any
    ) -> tuple[Select, list[tuple[sa.Column, bool]]]:
        """Apply ordering to the query statement and return order clauses for cursor pagination"""
        ...


class ModelConverter(Protocol):
    """Protocol for converting model to data objects"""

    def convert_to_data(self, model: Any) -> Any:
        """Convert model instance to data object"""
        ...


class GenericPaginator(Generic[TModel, TData, TFilters, TOrdering]):
    """Generic pagination logic that can be reused across different models"""

    def __init__(
        self,
        model_class: type[TModel],
        filter_applier: FilterApplier,
        ordering_applier: OrderingApplier,
        model_converter: ModelConverter,
        cursor_type_name: str = "Generic",
    ):
        self.model_class = model_class
        self.filter_applier = filter_applier
        self.ordering_applier = ordering_applier
        self.model_converter = model_converter
        self.cursor_type_name = cursor_type_name

    def build_lexicographic_cursor_conditions(
        self,
        order_clauses: list[tuple[sa.Column, bool]],
        cursor_uuid: uuid.UUID,
        pagination_order: Optional[ConnectionPaginationOrder],
    ) -> list[sa.sql.elements.BooleanClauseList]:
        """
        Build lexicographic cursor conditions for multiple ordering fields.
        Generic implementation that works with any model.
        """
        if not order_clauses:
            # Handle empty order_clauses case - compare by ID only
            id_column = getattr(self.model_class, "id")
            if pagination_order == ConnectionPaginationOrder.FORWARD:
                return [id_column > cursor_uuid]
            else:
                return [id_column < cursor_uuid]

        conditions = []

        # Cache subqueries to avoid duplication
        subquery_cache = {}

        def get_cursor_value_subquery(column):
            """Get or create cached subquery for cursor value"""
            if column not in subquery_cache:
                id_column = getattr(self.model_class, "id")
                subquery_cache[column] = (
                    sa.select(column).where(id_column == cursor_uuid).scalar_subquery()
                )
            return subquery_cache[column]

        # Build conditions for each level of the lexicographic ordering
        for i in range(len(order_clauses) + 1):  # +1 for the ID field
            condition_parts = []

            # Add equality conditions for all previous fields
            for j in range(i):
                order_column, desc = order_clauses[j]
                cursor_value_subq = get_cursor_value_subquery(order_column)
                condition_parts.append(order_column == cursor_value_subq)

            # Add the inequality condition for the current field
            if i < len(order_clauses):
                # Current field is one of the ordering fields
                order_column, desc = order_clauses[i]
                cursor_value_subq = get_cursor_value_subquery(order_column)

                # Determine the operator based on sort direction and pagination direction
                if pagination_order == ConnectionPaginationOrder.FORWARD:
                    if desc:
                        inequality_cond = order_column < cursor_value_subq
                    else:
                        inequality_cond = order_column > cursor_value_subq
                else:  # BACKWARD
                    if desc:
                        inequality_cond = order_column > cursor_value_subq
                    else:
                        inequality_cond = order_column < cursor_value_subq

                condition_parts.append(inequality_cond)
            else:
                # Final condition: all fields equal, compare by ID
                id_column = getattr(self.model_class, "id")
                if pagination_order == ConnectionPaginationOrder.FORWARD:
                    id_inequality_cond = id_column > cursor_uuid
                else:  # BACKWARD
                    id_inequality_cond = id_column < cursor_uuid

                condition_parts.append(id_inequality_cond)

            # Combine all parts with AND
            if condition_parts:
                if len(condition_parts) == 1:
                    conditions.append(condition_parts[0])
                else:
                    conditions.append(sa.and_(*condition_parts))

        return conditions

    async def paginate(
        self,
        db_session: sa.ext.asyncio.AsyncSession,
        pagination: PaginationOptions,
        ordering: Optional[TOrdering] = None,
        filters: Optional[TFilters] = None,
        select_options: Optional[list] = None,
    ) -> tuple[list[TData], int]:
        """
        Generic pagination method that works with any model.
        """
        # Build base query
        stmt = sa.select(self.model_class)
        if select_options:
            stmt = stmt.options(*select_options)
        count_stmt = sa.select(sa.func.count()).select_from(self.model_class)

        # Apply filters
        if filters is not None:
            stmt = self.filter_applier.apply_filters(stmt, filters)
            count_stmt = self.filter_applier.apply_filters(count_stmt, filters)

        offset_based_pagination = pagination.offset
        forward = pagination.forward
        backward = pagination.backward

        # Determine pagination mode
        if offset_based_pagination:
            offset = pagination.offset.offset if pagination.offset is not None else 0
            page_size = (
                offset_based_pagination.limit
                if offset_based_pagination.limit is not None
                else DEFAULT_PAGE_SIZE
            )

            # Apply ordering for offset-based pagination
            if ordering is not None:
                stmt, _ = self.ordering_applier.apply_ordering(stmt, ordering)

            # Default order by id for consistent pagination
            id_column = getattr(self.model_class, "id")
            stmt = stmt.order_by(id_column.asc())

            # Apply pagination
            stmt = stmt.offset(offset).limit(page_size)

            # Execute queries
            result = await db_session.execute(stmt)
            rows = result.scalars().all()
        else:
            # Cursor-based pagination
            after = forward.after if forward else None
            first = forward.first if forward else None
            before = backward.before if backward else None
            last = backward.last if backward else None

            connection_args = validate_connection_args(
                after=after,
                first=first,
                before=before,
                last=last,
            )

            cursor_id = connection_args.cursor
            pagination_order = connection_args.pagination_order
            page_size = connection_args.requested_page_size

            # Apply ordering for cursor-based pagination
            order_clauses: list[tuple[sa.Column, bool]] = []
            if ordering is not None:
                stmt, order_clauses = self.ordering_applier.apply_ordering(stmt, ordering)

            # Handle cursor-based pagination
            if cursor_id is not None:
                type_, cursor_id = resolve_global_id(cursor_id)
                if type_ != self.cursor_type_name:
                    raise InvalidCursorTypeError(f"Invalid cursor type: {type_}")

                cursor_uuid = uuid.UUID(cursor_id)

                # Build the lexicographic cursor conditions
                cursor_conditions = self.build_lexicographic_cursor_conditions(
                    order_clauses, cursor_uuid, pagination_order
                )

                # Apply cursor conditions with OR logic
                if cursor_conditions:
                    combined_cursor_condition = sa.or_(*cursor_conditions)
                    stmt = stmt.where(combined_cursor_condition)

            # Apply ordering based on pagination direction
            final_order_clauses = []
            id_column = getattr(self.model_class, "id")

            if pagination_order == ConnectionPaginationOrder.BACKWARD:
                # Reverse ordering for backward pagination
                for order_column, desc in order_clauses:
                    if desc:
                        final_order_clauses.append(order_column.asc())
                    else:
                        final_order_clauses.append(order_column.desc())
                final_order_clauses.append(id_column.desc())
            else:  # FORWARD or None
                for order_column, desc in order_clauses:
                    if desc:
                        final_order_clauses.append(order_column.desc())
                    else:
                        final_order_clauses.append(order_column.asc())
                final_order_clauses.append(id_column.asc())

            stmt = stmt.order_by(*final_order_clauses)

            # Apply limit
            stmt = stmt.limit(page_size)

            # Execute queries
            result = await db_session.execute(stmt)
            rows = result.scalars().all()

            # Reverse results for backward pagination
            if pagination_order == ConnectionPaginationOrder.BACKWARD:
                rows = list(reversed(rows))

        # Get total count
        count_result = await db_session.execute(count_stmt)
        total_count = count_result.scalar()

        # Convert models to data objects
        data_objects = [self.model_converter.convert_to_data(row) for row in rows]

        return data_objects, total_count


class ArtifactFilterApplier:
    """Applies artifact-specific filters to queries"""

    def apply_filters(self, stmt: Select, filters: ArtifactFilterOptions) -> Select:
        """Apply artifact filters to the query statement"""
        conditions = []

        if filters.artifact_type is not None:
            conditions.append(ArtifactRow.type == filters.artifact_type)
        if filters.status is not None:
            # Support multiple status values using IN clause
            status_values = [status.value for status in filters.status]
            conditions.append(ArtifactRow.status.in_(status_values))
        if filters.authorized is not None:
            conditions.append(ArtifactRow.authorized == filters.authorized)
        if filters.name is not None:
            conditions.append(ArtifactRow.name.ilike(f"%{filters.name}%"))
        if filters.registry_id is not None:
            conditions.append(ArtifactRow.registry_id == filters.registry_id)
        if filters.registry_type is not None:
            conditions.append(ArtifactRow.registry_type == filters.registry_type)
        if filters.source_registry_id is not None:
            conditions.append(ArtifactRow.source_registry_id == filters.source_registry_id)
        if filters.source_registry_type is not None:
            conditions.append(ArtifactRow.source_registry_type == filters.source_registry_type)

        # Apply conditions to the query
        if conditions:
            where_clause = sa.and_(*conditions)
            stmt = stmt.where(where_clause)

        return stmt


class ArtifactOrderingApplier:
    """Applies artifact-specific ordering to queries"""

    def apply_ordering(
        self, stmt: Select, ordering: ArtifactOrderingOptions
    ) -> tuple[Select, list[tuple[sa.Column, bool]]]:
        """Apply artifact ordering to the query statement"""
        order_clauses = []
        sql_order_clauses = []

        for field, desc in ordering.order_by:
            order_column = getattr(ArtifactRow, field.value, ArtifactRow.created_at)
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


class ArtifactRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

        # Initialize the generic paginator with artifact-specific components
        self._paginator = GenericPaginator[
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
    async def delete_artifact(self, artifact_id: uuid.UUID) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()

            await db_sess.delete(row)
            await db_sess.flush()

            return artifact_id

    @repository_decorator()
    async def cancel_import_artifact(self, artifact_id: uuid.UUID) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRow)
                .where(ArtifactRow.id == artifact_id)
                .values(status=ArtifactStatus.SCANNED)
            )
            await db_sess.execute(stmt)
            return artifact_id

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

        # Use the generic paginator with artifact-specific select options
        async with self._db.begin_session() as db_sess:
            return await self._paginator.paginate(
                db_session=db_sess,
                pagination=pagination,
                ordering=ordering,
                filters=filters,
                select_options=[selectinload(ArtifactRow.version_rows)],
            )
