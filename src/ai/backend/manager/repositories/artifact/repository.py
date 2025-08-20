import uuid
from typing import Optional

import sqlalchemy as sa

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
from ai.backend.manager.api.gql.base import resolve_global_id
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRegistryType,
    ArtifactRevisionData,
    ArtifactStatus,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow
from ai.backend.manager.models.base import DEFAULT_PAGE_SIZE, validate_connection_args
from ai.backend.manager.models.gql_relay import ConnectionPaginationOrder
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
                    await db_sess.refresh(artifact_row, attribute_names=["updated_at"])

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
                    existing_revision.created_at = model.created_at
                    existing_revision.updated_at = model.modified_at

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
            # Delete all associations
            await db_sess.execute(
                sa.delete(AssociationArtifactsStoragesData).where(
                    AssociationArtifactsStoragesData.artifact_id == artifact_id
                )
            )

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
    async def update_artifact_status(
        self, artifact_id: uuid.UUID, status: ArtifactStatus
    ) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = sa.update(ArtifactRow).where(ArtifactRow.id == artifact_id).values(status=status)
            await db_sess.execute(stmt)
            return artifact_id

    @repository_decorator()
    async def update_artifact_bytesize(self, artifact_id: uuid.UUID, size: int) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = sa.update(ArtifactRow).where(ArtifactRow.id == artifact_id).values(size=size)
            await db_sess.execute(stmt)
            return artifact_id

    @repository_decorator()
    async def update_artifact_readme(self, artifact_id: uuid.UUID, readme: str) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = sa.update(ArtifactRow).where(ArtifactRow.id == artifact_id).values(readme=readme)
            await db_sess.execute(stmt)
            return artifact_id

    @repository_decorator()
    async def list_artifacts_paginated(
        self,
        *,
        pagination: PaginationOptions,
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
        offset_based_pagination = pagination.offset
        forward = pagination.forward
        backward = pagination.backward

        if ordering is None:
            ordering = ArtifactOrderingOptions()
        if filters is None:
            filters = ArtifactFilterOptions()
        async with self._db.begin_session() as db_sess:
            # Build base query
            stmt = sa.select(ArtifactRow)
            count_stmt = sa.select(sa.func.count()).select_from(ArtifactRow)

            # Apply filters
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

            # Apply conditions to both queries
            if conditions:
                where_clause = sa.and_(*conditions)
                stmt = stmt.where(where_clause)
                count_stmt = count_stmt.where(where_clause)

            # Determine pagination mode
            if offset_based_pagination:
                offset = pagination.offset.offset if pagination.offset is not None else 0
                page_size = (
                    offset_based_pagination.limit
                    if offset_based_pagination.limit is not None
                    else DEFAULT_PAGE_SIZE
                )

                # Apply multiple ordering fields
                order_clauses = []
                for field, desc in ordering.order_by:
                    order_column = getattr(ArtifactRow, field.value, ArtifactRow.created_at)
                    if desc:
                        order_clauses.append(order_column.desc())
                    else:
                        order_clauses.append(order_column.asc())
                stmt = stmt.order_by(*order_clauses)

                # Default order by id for consistent pagination
                stmt = stmt.order_by(ArtifactRow.id.asc())

                # Apply pagination
                stmt = stmt.offset(offset).limit(page_size)
            else:
                # Extract pagination parameters from forward/backward options
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

                # Apply multiple ordering fields for connection pagination
                order_clauses = []
                for field, desc in ordering.order_by:
                    order_column = getattr(ArtifactRow, field.value, ArtifactRow.created_at)
                    order_clauses.append((order_column, desc))

                # Handle cursor-based pagination
                if cursor_id is not None:
                    type_, cursor_id = resolve_global_id(cursor_id)
                    if type_ != "Artifact":
                        raise InvalidCursorTypeError(f"Invalid cursor type: {type_}")

                    cursor_uuid = uuid.UUID(cursor_id)

                    # Build lexicographic cursor conditions for proper multi-field ordering
                    # This implements the same logic as generate_sql_info_for_gql_connection

                    def build_lexicographic_cursor_conditions(
                        order_clauses,
                        cursor_uuid,
                        pagination_order,
                    ):
                        """
                        Build lexicographic cursor conditions for multiple ordering fields.

                        For proper multi-field ordering, we need to build conditions that represent
                        lexicographic ordering. For fields [A, B, C], the condition should be:
                        (A > cursor_A) OR
                        (A = cursor_A AND B > cursor_B) OR
                        (A = cursor_A AND B = cursor_B AND C > cursor_C) OR
                        (A = cursor_A AND B = cursor_B AND C = cursor_C AND id > cursor_id)

                        The direction operators (>, <) depend on the sort direction and pagination direction.
                        """
                        if not order_clauses:
                            return []

                        conditions = []

                        # Build conditions for each level of the lexicographic ordering
                        for i in range(len(order_clauses) + 1):  # +1 for the ID field
                            condition_parts = []

                            # Add equality conditions for all previous fields
                            for j in range(i):
                                order_column, desc = order_clauses[j]
                                cursor_value_subq = (
                                    sa.select(order_column)
                                    .where(ArtifactRow.id == cursor_uuid)
                                    .scalar_subquery()
                                )
                                condition_parts.append(order_column == cursor_value_subq)

                            # Add the inequality condition for the current field
                            if i < len(order_clauses):
                                # Current field is one of the ordering fields
                                order_column, desc = order_clauses[i]
                                cursor_value_subq = (
                                    sa.select(order_column)
                                    .where(ArtifactRow.id == cursor_uuid)
                                    .scalar_subquery()
                                )

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
                                if pagination_order == ConnectionPaginationOrder.FORWARD:
                                    id_inequality_cond = ArtifactRow.id > cursor_uuid
                                else:  # BACKWARD
                                    id_inequality_cond = ArtifactRow.id < cursor_uuid

                                condition_parts.append(id_inequality_cond)

                            # Combine all parts with AND
                            if condition_parts:
                                if len(condition_parts) == 1:
                                    conditions.append(condition_parts[0])
                                else:
                                    conditions.append(sa.and_(*condition_parts))

                        return conditions

                    # Build the lexicographic cursor conditions
                    cursor_conditions = build_lexicographic_cursor_conditions(
                        order_clauses, cursor_uuid, pagination_order
                    )

                    # Apply cursor conditions with OR logic
                    if cursor_conditions:
                        combined_cursor_condition = sa.or_(*cursor_conditions)
                        stmt = stmt.where(combined_cursor_condition)

                # Apply ordering based on pagination direction
                final_order_clauses = []
                if pagination_order == ConnectionPaginationOrder.BACKWARD:
                    # Reverse ordering for backward pagination
                    for order_column, desc in order_clauses:
                        if desc:
                            final_order_clauses.append(order_column.asc())
                        else:
                            final_order_clauses.append(order_column.desc())
                    final_order_clauses.append(ArtifactRow.id.desc())
                else:  # FORWARD or None
                    for order_column, desc in order_clauses:
                        if desc:
                            final_order_clauses.append(order_column.desc())
                        else:
                            final_order_clauses.append(order_column.asc())
                    final_order_clauses.append(ArtifactRow.id.asc())

                stmt = stmt.order_by(*final_order_clauses)

                # Apply limit
                stmt = stmt.limit(page_size)

            # Execute queries
            result = await db_sess.execute(stmt)
            rows = result.scalars().all()

            # Reverse results for backward pagination
            if (
                pagination.offset is None
                and connection_args.pagination_order == ConnectionPaginationOrder.BACKWARD
            ):
                rows = list(reversed(rows))

            count_result = await db_sess.execute(count_stmt)
            total_count = count_result.scalar()

            artifacts = [row.to_dataclass() for row in rows]
            return artifacts, total_count
