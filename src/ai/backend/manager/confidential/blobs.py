from __future__ import annotations

import hashlib

import sqlalchemy as sa

from ai.backend.manager.errors.confidential import MeasuredBlobNotFound
from ai.backend.manager.models.confidential.row import ConfidentialMeasuredBlobRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class MeasuredBlobStore:
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def publish(
        self, endpoint: str, image_digest: str, profile_version: str, blob: bytes
    ) -> str:
        blob_digest = hashlib.sha384(blob).hexdigest()
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                sa.delete(ConfidentialMeasuredBlobRow).where(
                    (ConfidentialMeasuredBlobRow.endpoint == endpoint)
                    & (ConfidentialMeasuredBlobRow.image_digest == image_digest)
                    & (ConfidentialMeasuredBlobRow.profile_version == profile_version)
                )
            )
            db_session.add(
                ConfidentialMeasuredBlobRow(
                    endpoint=endpoint,
                    image_digest=image_digest,
                    profile_version=profile_version,
                    blob_digest=blob_digest,
                    blob=blob,
                )
            )
        return blob_digest

    async def fetch(
        self, endpoint: str, image_digest: str, profile_version: str
    ) -> tuple[bytes, str]:
        async with self._db.begin_readonly_session() as db_session:
            row = await db_session.get(
                ConfidentialMeasuredBlobRow, (endpoint, image_digest, profile_version)
            )
        if row is None:
            raise MeasuredBlobNotFound(
                extra_msg=f"no blob for {image_digest} at profile {profile_version} on {endpoint}"
            )
        return row.blob, hashlib.sha384(row.blob).hexdigest()
