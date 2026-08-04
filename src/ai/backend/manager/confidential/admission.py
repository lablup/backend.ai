from __future__ import annotations

import uuid
from typing import Final

import sqlalchemy as sa

from ai.backend.manager.errors.confidential import AdmissionBeltExceeded
from ai.backend.manager.models.confidential.row import ConfidentialNonceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

INTERIM_BELT_ENABLED: Final = True


async def check_admission_belt(
    db: ExtendedAsyncSAEngine,
    *,
    endpoint: str,
    image_digest: str,
    profile_version: str,
    limit: int,
    session_id: uuid.UUID,
) -> None:
    if not INTERIM_BELT_ENABLED or limit <= 0:
        return
    async with db.begin_readonly_session() as db_session:
        concurrent = await db_session.scalar(
            sa.select(sa.func.count())
            .select_from(ConfidentialNonceRow)
            .where(
                (ConfidentialNonceRow.endpoint == endpoint)
                & (ConfidentialNonceRow.image_digest == image_digest)
                & (ConfidentialNonceRow.profile_version == profile_version)
                & (ConfidentialNonceRow.session_id != session_id)
            )
        )
    if (concurrent or 0) >= limit:
        raise AdmissionBeltExceeded(
            extra_msg=(
                f"{concurrent} confidential sessions already run image {image_digest}"
                f" at profile {profile_version}; the interim belt allows {limit}."
                " It is removed by deleting this module and its single call site in"
                " confidential/provisioning.py, once the launch-nonce mechanism is"
                " demonstrated on the rig."
            )
        )
