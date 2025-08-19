import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import sqlalchemy as sa

from ai.backend.common.data.storage.registries.types import ModelData, ModelTarget
from ai.backend.common.exception import (
    ArtifactAssociationDeletionError,
    ArtifactAssociationNotFoundError,
    ArtifactNotFoundError,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactRegistryType,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow
from ai.backend.manager.models.base import DEFAULT_PAGE_SIZE, validate_connection_args
from ai.backend.manager.models.gql_relay import ConnectionPaginationOrder
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for artifact repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.ARTIFACT)


class ArtifactOrderingField(Enum):
    """Available fields for ordering artifacts."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NAME = "name"
    SIZE = "size"
    TYPE = "type"
    STATUS = "status"
    AUTHORIZED = "authorized"
    REGISTRY_TYPE = "registry_type"
    SOURCE_REGISTRY_TYPE = "source_registry_type"
    VERSION = "version"


@dataclass
class OffsetBasedPaginationOptions:
    """Standard offset/limit pagination options."""

    offset: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class ForwardPaginationOptions:
    """Forward pagination: fetch items after a given cursor."""

    after: Optional[str] = None
    first: Optional[int] = None


@dataclass
class BackwardPaginationOptions:
    """Backward pagination: fetch items before a given cursor."""

    before: Optional[str] = None
    last: Optional[int] = None


@dataclass
class ArtifactOrderingOptions:
    """Ordering options for artifact queries."""

    order_by: ArtifactOrderingField = ArtifactOrderingField.CREATED_AT
    order_desc: bool = True


@dataclass
class ArtifactFilterOptions:
    """Filtering options for artifacts."""

    artifact_type: Optional[ArtifactType] = None
    status: Optional[ArtifactStatus] = None
    authorized: Optional[bool] = None
    name_filter: Optional[str] = None
    registry_id: Optional[uuid.UUID] = None
    registry_type: Optional[ArtifactRegistryType] = None
    source_registry_id: Optional[uuid.UUID] = None
    source_registry_type: Optional[ArtifactRegistryType] = None


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
    async def get_artifact_by_model_target(self, model_target: ModelTarget) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(
                    sa.and_(
                        ArtifactRow.name == model_target.model_id,
                        ArtifactRow.version == model_target.revision,
                    )
                )
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()
            return row.to_dataclass()

    @repository_decorator()
    async def upsert_huggingface_model_artifacts(
        self,
        model_list: list[ModelData],
        registry_id: uuid.UUID,
        source_registry_id: uuid.UUID,
        source_registry_type: ArtifactRegistryType,
    ) -> list[ArtifactData]:
        async with self._db.begin_session() as db_sess:
            result = []

            for model in model_list:
                # Check if artifact with same model_id and registry_id already exists
                existing_stmt = sa.select(ArtifactRow).where(
                    sa.and_(
                        ArtifactRow.name == model.id,
                        ArtifactRow.registry_id == registry_id,
                    )
                )
                existing_result = await db_sess.execute(existing_stmt)
                existing_artifact = existing_result.scalar_one_or_none()

                if existing_artifact is not None:
                    # Update existing artifact
                    existing_artifact.source_registry_id = source_registry_id
                    existing_artifact.source_registry_type = source_registry_type
                    if model.modified_at:
                        existing_artifact.updated_at = model.modified_at
                    existing_artifact.authorized = False
                    existing_artifact.version = model.revision
                    # existing_artifact.status = ArtifactStatus.SCANNED.value

                    await db_sess.flush()
                    await db_sess.refresh(existing_artifact, attribute_names=["updated_at"])
                    result.append(existing_artifact.to_dataclass())
                else:
                    # Insert new artifact
                    new_artifact = ArtifactRow.from_huggingface_model_data(
                        model,
                        registry_id=registry_id,
                        source_registry_id=source_registry_id,
                        source_registry_type=source_registry_type,
                    )
                    db_sess.add(new_artifact)
                    await db_sess.flush()
                    await db_sess.refresh(
                        new_artifact, attribute_names=["id", "created_at", "updated_at"]
                    )
                    result.append(new_artifact.to_dataclass())

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
    async def authorize_artifact(self, artifact_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()

            row.authorized = True
            await db_sess.flush()
            await db_sess.refresh(row, attribute_names=["updated_at"])
            return row.to_dataclass()

    @repository_decorator()
    async def unauthorize_artifact(self, artifact_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row: ArtifactRow = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError()

            row.authorized = False
            await db_sess.flush()
            await db_sess.refresh(row, attribute_names=["updated_at"])
            return row.to_dataclass()

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
        pagination: Optional[OffsetBasedPaginationOptions] = None,
        forward: Optional[ForwardPaginationOptions] = None,
        backward: Optional[BackwardPaginationOptions] = None,
        ordering: Optional[ArtifactOrderingOptions] = None,
        filters: Optional[ArtifactFilterOptions] = None,
    ) -> tuple[list[ArtifactData], int]:
        """List artifacts with pagination and filtering.

        Args:
            pagination: Standard offset/limit pagination options
            forward: Forward pagination options (after, first)
            backward: Backward pagination options (before, last)
            ordering: Ordering options for the query
            filters: Filtering options for artifacts

        Returns:
            Tuple of (artifacts list, total count)
        """
        # Set defaults
        if pagination is None:
            pagination = OffsetBasedPaginationOptions()
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
                conditions.append(ArtifactRow.status == filters.status.value)
            if filters.authorized is not None:
                conditions.append(ArtifactRow.authorized == filters.authorized)
            if filters.name_filter is not None:
                conditions.append(ArtifactRow.name.ilike(f"%{filters.name_filter}%"))
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
            if pagination.offset is not None:
                # Standard offset/limit pagination
                page_size = pagination.limit if pagination.limit is not None else DEFAULT_PAGE_SIZE

                # Apply ordering
                order_column = getattr(ArtifactRow, ordering.order_by.value, ArtifactRow.created_at)
                if ordering.order_desc:
                    stmt = stmt.order_by(order_column.desc())
                else:
                    stmt = stmt.order_by(order_column.asc())

                # Default order by id for consistent pagination
                stmt = stmt.order_by(ArtifactRow.id.asc())

                # Apply pagination
                stmt = stmt.offset(pagination.offset).limit(page_size)

            else:
                # GraphQL connection pagination
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

                # Apply primary ordering
                order_column = getattr(ArtifactRow, ordering.order_by.value, ArtifactRow.created_at)

                # Handle cursor-based pagination
                if cursor_id is not None:
                    try:
                        cursor_uuid = uuid.UUID(cursor_id)

                        # Get the cursor row to compare against
                        cursor_stmt = sa.select(ArtifactRow).where(ArtifactRow.id == cursor_uuid)
                        cursor_result = await db_sess.execute(cursor_stmt)
                        cursor_row = cursor_result.scalar_one_or_none()

                        if cursor_row is not None:
                            cursor_order_value = getattr(cursor_row, ordering.order_by.value)

                            # Build cursor condition based on pagination direction
                            if pagination_order == ConnectionPaginationOrder.FORWARD:
                                if ordering.order_desc:
                                    cursor_condition = (order_column < cursor_order_value) | (
                                        (order_column == cursor_order_value)
                                        & (ArtifactRow.id > cursor_uuid)
                                    )
                                else:
                                    cursor_condition = (order_column > cursor_order_value) | (
                                        (order_column == cursor_order_value)
                                        & (ArtifactRow.id > cursor_uuid)
                                    )
                            else:  # BACKWARD
                                if ordering.order_desc:
                                    cursor_condition = (order_column > cursor_order_value) | (
                                        (order_column == cursor_order_value)
                                        & (ArtifactRow.id < cursor_uuid)
                                    )
                                else:
                                    cursor_condition = (order_column < cursor_order_value) | (
                                        (order_column == cursor_order_value)
                                        & (ArtifactRow.id < cursor_uuid)
                                    )

                            stmt = stmt.where(cursor_condition)

                    except ValueError:
                        # Invalid UUID cursor, ignore
                        pass

                # Apply ordering based on pagination direction
                if pagination_order == ConnectionPaginationOrder.BACKWARD:
                    # Reverse ordering for backward pagination
                    if ordering.order_desc:
                        stmt = stmt.order_by(order_column.asc(), ArtifactRow.id.desc())
                    else:
                        stmt = stmt.order_by(order_column.desc(), ArtifactRow.id.desc())
                else:  # FORWARD or None
                    if ordering.order_desc:
                        stmt = stmt.order_by(order_column.desc(), ArtifactRow.id.asc())
                    else:
                        stmt = stmt.order_by(order_column.asc(), ArtifactRow.id.asc())

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
