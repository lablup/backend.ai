from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Final, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.confidential.shim import AuthorisationShim
from ai.backend.manager.errors.confidential import ReferenceValueRejected
from ai.backend.manager.models.confidential.row import (
    ConfidentialNonceRow,
    ConfidentialReferenceValueRow,
)
from ai.backend.manager.models.confidential.types import ReferenceValueState
from ai.backend.manager.models.scaling_group.types import ConfidentialScalingGroupOpts
from ai.backend.manager.models.session import DEAD_SESSION_STATUSES, SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_COEXISTENCE: Final = timedelta(days=14)
REQUIRED_MEASUREMENTS: Final = ("mr_config_id", "mr_td", "rtmr_1", "rtmr_2", "xfam")


def unpinned_measurements(measurements: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_MEASUREMENTS if not measurements.get(field)]


def carrying_live_session(endpoint: str) -> sa.ColumnElement[bool]:
    return sa.exists(
        sa.select(sa.literal(1))
        .select_from(
            sa.join(
                ConfidentialNonceRow,
                SessionRow,
                SessionRow.id == ConfidentialNonceRow.session_id,
            )
        )
        .where(
            (ConfidentialNonceRow.endpoint == endpoint)
            & (ConfidentialNonceRow.image_digest == ConfidentialReferenceValueRow.image_digest)
            & (
                ConfidentialNonceRow.profile_version
                == ConfidentialReferenceValueRow.profile_version
            )
            & SessionRow.status.not_in(DEAD_SESSION_STATUSES)
        )
        .correlate(ConfidentialReferenceValueRow)
    )


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
        missing = unpinned_measurements(measurements)
        if missing:
            raise ReferenceValueRejected(
                extra_msg=(
                    f"measurements leave {', '.join(missing)} unpinned,"
                    " so the composed release policy would not gate on them"
                )
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
                            & (
                                (ConfidentialReferenceValueRow.coexistence_until > now)
                                | carrying_live_session(endpoint)
                            )
                        )
                    )
                )
                .order_by(ConfidentialReferenceValueRow.created_at)
            )
            return list(rows.all())

    async def invalidate_unpinned(self) -> list[tuple[uuid.UUID, str, list[str]]]:
        async with self._db.begin_session() as db_session:
            rows = await db_session.scalars(
                sa.select(ConfidentialReferenceValueRow).where(
                    ConfidentialReferenceValueRow.state.in_((
                        ReferenceValueState.ACTIVE,
                        ReferenceValueState.SUPERSEDED,
                    ))
                )
            )
            invalidated = []
            for row in rows.all():
                missing = unpinned_measurements(row.measurements)
                if not missing:
                    continue
                row.state = ReferenceValueState.INVALID
                row.coexistence_until = datetime.now(UTC)
                invalidated.append((row.id, row.endpoint, missing))
            return invalidated

    async def close_expired_windows(self, endpoint: str) -> int:
        now = datetime.now(UTC)
        async with self._db.begin_session() as db_session:
            result = await db_session.execute(
                sa.update(ConfidentialReferenceValueRow)
                .where(
                    (ConfidentialReferenceValueRow.endpoint == endpoint)
                    & (ConfidentialReferenceValueRow.state == ReferenceValueState.SUPERSEDED)
                    & (ConfidentialReferenceValueRow.coexistence_until <= now)
                    & ~carrying_live_session(endpoint)
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
        live = sa.select(ConfidentialNonceRow.session_id).join(
            SessionRow, SessionRow.id == ConfidentialNonceRow.session_id
        )
        async with self._db.begin_readonly_session() as db_session:
            carried = await db_session.scalars(
                live.where(
                    (ConfidentialNonceRow.reference_value_id == row.id)
                    & SessionRow.status.not_in(DEAD_SESSION_STATUSES)
                )
            )
            unattributed = await db_session.scalars(
                live.where(
                    ConfidentialNonceRow.reference_value_id.is_(None)
                    & (ConfidentialNonceRow.endpoint == row.endpoint)
                    & (ConfidentialNonceRow.image_digest == row.image_digest)
                    & (ConfidentialNonceRow.profile_version == row.profile_version)
                    & SessionRow.status.not_in(DEAD_SESSION_STATUSES)
                )
            )
            drained = list(carried.all())
            blind = list(unattributed.all())
        if blind:
            log.warning(
                "confidential: {} live sessions on image {} at profile {} never named the"
                " reference value that admitted them, so retiring {} cannot speak for them: {}",
                len(blind),
                row.image_digest,
                row.profile_version,
                row.id,
                blind,
            )
        return drained
