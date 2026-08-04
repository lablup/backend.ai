from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Final, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.manager.confidential.shim import AuthorisationShim
from ai.backend.manager.errors.confidential import ReferenceValueRejected
from ai.backend.manager.models.confidential.row import (
    ConfidentialNonceRow,
    ConfidentialReferenceValueRow,
)
from ai.backend.manager.models.confidential.types import ReferenceValueState
from ai.backend.manager.models.scaling_group.types import ConfidentialScalingGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

DEFAULT_COEXISTENCE: Final = timedelta(days=14)


def bundle_bytes(
    endpoint: str, image_digest: str, profile_version: str, measurements: dict[str, Any]
) -> bytes:
    return json.dumps(
        {
            "endpoint": endpoint,
            "image_digest": image_digest,
            "profile_version": profile_version,
            "measurements": measurements,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class ReferenceValueStore:
    def __init__(self, db: ExtendedAsyncSAEngine, shim: AuthorisationShim) -> None:
        self._db = db
        self._shim = shim

    async def register(
        self,
        opts: ConfidentialScalingGroupOpts,
        *,
        attested_identity: str,
        image_digest: str,
        profile_version: str,
        measurements: dict[str, Any],
        pipeline_signature: str,
        supersedes: uuid.UUID | None,
        coexistence: timedelta | None,
    ) -> ConfidentialReferenceValueRow:
        if not opts.attested_identity or attested_identity != opts.attested_identity:
            raise ReferenceValueRejected(
                extra_msg="registration is reachable only under the manager's attested machine identity"
            )
        bundle = bundle_bytes(opts.broker_endpoint, image_digest, profile_version, measurements)
        await self._shim.authorise_bundle(opts, "reference-value", bundle, pipeline_signature)
        window = coexistence if coexistence is not None else DEFAULT_COEXISTENCE
        async with self._db.begin_session() as db_session:
            if supersedes is not None:
                superseded = await db_session.get(ConfidentialReferenceValueRow, supersedes)
                if superseded is None or superseded.endpoint != opts.broker_endpoint:
                    raise ReferenceValueRejected(
                        extra_msg="superseded reference value is unknown at this broker endpoint"
                    )
                superseded.state = ReferenceValueState.SUPERSEDED
                superseded.coexistence_until = datetime.now(UTC) + window
            row = ConfidentialReferenceValueRow(
                endpoint=opts.broker_endpoint,
                image_digest=image_digest,
                profile_version=profile_version,
                measurements=measurements,
                pipeline_signature=pipeline_signature,
                registered_by=attested_identity,
                state=ReferenceValueState.ACTIVE,
                supersedes=supersedes,
                coexistence_until=None,
            )
            db_session.add(row)
            await db_session.flush()
            return row

    async def admissible(self, endpoint: str) -> list[ConfidentialReferenceValueRow]:
        now = datetime.now(UTC)
        async with self._db.begin_readonly_session() as db_session:
            rows = await db_session.scalars(
                sa.select(ConfidentialReferenceValueRow)
                .where(
                    (ConfidentialReferenceValueRow.endpoint == endpoint)
                    & (
                        (ConfidentialReferenceValueRow.state == ReferenceValueState.ACTIVE)
                        | (
                            (ConfidentialReferenceValueRow.state == ReferenceValueState.SUPERSEDED)
                            & (ConfidentialReferenceValueRow.coexistence_until > now)
                        )
                    )
                )
                .order_by(ConfidentialReferenceValueRow.created_at)
            )
            return list(rows.all())

    async def close_expired_windows(self, endpoint: str) -> int:
        now = datetime.now(UTC)
        async with self._db.begin_session() as db_session:
            result = await db_session.execute(
                sa.update(ConfidentialReferenceValueRow)
                .where(
                    (ConfidentialReferenceValueRow.endpoint == endpoint)
                    & (ConfidentialReferenceValueRow.state == ReferenceValueState.SUPERSEDED)
                    & (ConfidentialReferenceValueRow.coexistence_until <= now)
                )
                .values(state=ReferenceValueState.RETIRED)
            )
            return cast(CursorResult[Any], result).rowcount

    async def retire(self, value_id: uuid.UUID) -> ConfidentialReferenceValueRow:
        async with self._db.begin_session() as db_session:
            row = await db_session.get(ConfidentialReferenceValueRow, value_id)
            if row is None:
                raise ReferenceValueRejected(extra_msg="unknown reference value")
            row.state = ReferenceValueState.RETIRED
            row.coexistence_until = datetime.now(UTC)
            await db_session.flush()
            return row

    async def sessions_on(self, row: ConfidentialReferenceValueRow) -> list[uuid.UUID]:
        async with self._db.begin_readonly_session() as db_session:
            sessions = await db_session.scalars(
                sa.select(ConfidentialNonceRow.session_id).where(
                    (ConfidentialNonceRow.endpoint == row.endpoint)
                    & (ConfidentialNonceRow.image_digest == row.image_digest)
                    & (ConfidentialNonceRow.profile_version == row.profile_version)
                )
            )
            return list(sessions.all())
