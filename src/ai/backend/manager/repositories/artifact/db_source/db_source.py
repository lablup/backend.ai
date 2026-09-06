import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.ext.asyncio import async_sessionmaker

from ai.backend.common.data.artifact.types import VerificationStepResult
from ai.backend.common.data.storage.types import ArtifactStorageType
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactStatus,
)
from ai.backend.manager.data.association.types import AssociationArtifactsStoragesData
from ai.backend.manager.errors.artifact import (
    ArtifactAssociationDeletionError,
    ArtifactAssociationNotFoundError,
    ArtifactNotFoundError,
    ArtifactNotVerified,
    ArtifactRevisionNotFoundError,
    ArtifactUpdateError,
)
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class ArtifactDBSource:
    """Database source for artifact-related operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_artifact_by_id(self, artifact_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(ArtifactRow.id == artifact_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(f"Artifact with ID {artifact_id} not found")
            return row.to_dataclass()

    async def get_model_artifact(self, model_id: str, registry_id: uuid.UUID) -> ArtifactData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRow).where(
                    sa.and_(ArtifactRow.name == model_id, ArtifactRow.registry_id == registry_id)
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactNotFoundError(
                    f"Artifact with model ID {model_id} not found under registry {registry_id}"
                )
            return row.to_dataclass()

    async def get_artifact_revision(
        self, artifact_id: uuid.UUID, revision: str
    ) -> ArtifactRevisionData:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(
                    sa.and_(
                        ArtifactRevisionRow.artifact_id == artifact_id,
                        ArtifactRevisionRow.version == revision,
                    )
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError(f"Revision {revision} not found")
            return row.to_dataclass()

    async def list_artifact_revisions(self, artifact_id: uuid.UUID) -> list[ArtifactRevisionData]:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.artifact_id == artifact_id)
            )
            rows = list(result.scalars().all())
            return [row.to_dataclass() for row in rows]

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
            existing = result.scalar_one()

            return AssociationArtifactsStoragesData(
                id=existing,
                artifact_revision_id=artifact_revision_id,
                storage_namespace_id=storage_namespace_id,
            )

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
            existing_row = select_result.scalar_one_or_none()
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

            if cast(CursorResult[Any], delete_result).rowcount == 0:
                raise ArtifactAssociationDeletionError("Failed to delete association")

            return association_data

    async def approve_artifact(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.id == revision_id)
            )
            row = result.scalar_one_or_none()
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
            updated_row = result.scalars().one_or_none()
            if updated_row is None:
                raise ArtifactUpdateError()

            return updated_row.to_dataclass()

    async def reject_artifact(self, revision_id: uuid.UUID) -> ArtifactRevisionData:
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow).where(ArtifactRevisionRow.id == revision_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise ArtifactRevisionNotFoundError()

            update_stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == revision_id)
                .values(status=ArtifactStatus.REJECTED.value)
                .returning(ArtifactRevisionRow)
            )

            result = await db_sess.execute(update_stmt)
            updated_row = result.scalars().one_or_none()
            if updated_row is None:
                raise ArtifactUpdateError()

            return updated_row.to_dataclass()

    async def reset_artifact_revision_status(self, revision_id: uuid.UUID) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == revision_id)
                .values(status=ArtifactStatus.SCANNED)
            )
            await db_sess.execute(stmt)
            return revision_id

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

    async def update_artifact_revision_remote_status(
        self, artifact_revision_id: uuid.UUID, remote_status: ArtifactRemoteStatus
    ) -> uuid.UUID:
        async with self._db.begin_session() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(remote_status=remote_status)
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

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
            rows = list(result.scalars().all())
            return [row.to_dataclass() for row in rows]

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
            rows = list(result.scalars().all())
            return [row.to_dataclass() for row in rows]

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

    async def update_artifact_revision_verification_result(
        self,
        artifact_revision_id: uuid.UUID,
        verification_result: VerificationStepResult,
    ) -> uuid.UUID:
        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(verification_result=verification_result.model_dump())
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

    async def update_artifact_revision_digest(
        self, artifact_revision_id: uuid.UUID, digest: str
    ) -> uuid.UUID:
        async with self._begin_session_read_committed() as db_sess:
            stmt = (
                sa.update(ArtifactRevisionRow)
                .where(ArtifactRevisionRow.id == artifact_revision_id)
                .values(digest=digest)
            )
            await db_sess.execute(stmt)
            return artifact_revision_id

    async def get_artifact_revision_readme(self, artifact_revision_id: uuid.UUID) -> str | None:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.execute(
                sa.select(ArtifactRevisionRow.readme).where(
                    ArtifactRevisionRow.id == artifact_revision_id
                )
            )
            return result.scalar_one_or_none()

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
                sess_factory = async_sessionmaker(
                    bind=conn_with_isolation,
                    expire_on_commit=False,
                )
                session = sess_factory()
                yield session
                await session.commit()
