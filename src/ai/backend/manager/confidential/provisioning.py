from __future__ import annotations

import logging
import secrets
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.confidential.admission import check_admission_belt
from ai.backend.manager.confidential.broker import BrokerClient, BrokerTarget
from ai.backend.manager.confidential.payloads import TIME_RESOURCE, attested_time
from ai.backend.manager.confidential.shim import AuthorisationShim
from ai.backend.manager.errors.confidential import BrokerUnreachable
from ai.backend.manager.metrics.confidential import ConfidentialMetricObserver
from ai.backend.manager.models.confidential.row import (
    ConfidentialNonceRow,
    ConfidentialSessionResourceRow,
)
from ai.backend.manager.models.confidential.types import (
    DecisionActor,
    DecisionVerdict,
    SessionResourceKind,
)
from ai.backend.manager.models.scaling_group.types import (
    NONCE_RESIDUAL_DISCLOSURE,
    ConfidentialScalingGroupOpts,
)
from ai.backend.manager.models.session import DEAD_SESSION_STATUSES, SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

RECONCILE_INTERVAL: Final = 300.0


@dataclass(frozen=True)
class SessionProvisioning:
    session_id: uuid.UUID
    nonce: str
    quota: int
    shim_url: str
    resource_paths: list[str]
    residual: str = NONCE_RESIDUAL_DISCLOSURE

    def path_of(self, tag: str) -> str | None:
        return next((p for p in self.resource_paths if p.rsplit("/", 1)[-1] == tag), None)


class SessionResourceProvisioner:
    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        broker: BrokerClient,
        shim: AuthorisationShim,
    ) -> None:
        self._db = db
        self._broker = broker
        self._shim = shim

    async def provision(
        self,
        opts: ConfidentialScalingGroupOpts,
        *,
        session_id: uuid.UUID,
        domain_name: str,
        image_digest: str,
        profile_version: str,
        member_count: int,
        resources: Mapping[str, tuple[SessionResourceKind, bytes]],
    ) -> SessionProvisioning:
        await check_admission_belt(
            self._db,
            endpoint=opts.broker_endpoint,
            image_digest=image_digest,
            profile_version=profile_version,
            limit=opts.admission_limit_per_image,
            session_id=session_id,
        )
        async with self._db.begin_readonly_session() as db_session:
            held = await db_session.scalar(
                sa.select(ConfidentialNonceRow.nonce).where(
                    ConfidentialNonceRow.session_id == session_id
                )
            )
        nonce = held or secrets.token_urlsafe(24)
        target = BrokerTarget.of(opts)
        await self._broker.put_resource(target, TIME_RESOURCE, attested_time())
        written: list[str] = []
        for tag, (kind, payload) in resources.items():
            path = await self._shim.authorise_session_path(
                domain_name, session_id, nonce, f"{domain_name}/{session_id}.{nonce}/{tag}"
            )
            await self._broker.put_resource(target, path, payload)
            written.append(path)
            async with self._db.begin_session() as db_session:
                await db_session.execute(
                    pg_insert(ConfidentialSessionResourceRow)
                    .values(
                        session_id=session_id,
                        endpoint=opts.broker_endpoint,
                        resource_path=path,
                        kind=kind,
                    )
                    .on_conflict_do_nothing(constraint="uq_conf_resource_path")
                )
            await self._shim.record(
                actor=DecisionActor.MANAGER,
                verdict=DecisionVerdict.ALLOWED,
                resource_path=path,
                session_id=session_id,
                nonce=nonce,
            )
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                sa.delete(ConfidentialNonceRow).where(ConfidentialNonceRow.session_id == session_id)
            )
            db_session.add(
                ConfidentialNonceRow(
                    session_id=session_id,
                    nonce=nonce,
                    endpoint=opts.broker_endpoint,
                    domain_name=domain_name,
                    image_digest=image_digest,
                    profile_version=profile_version,
                    quota=member_count,
                    claims_used=0,
                )
            )
        return SessionProvisioning(
            session_id=session_id,
            nonce=nonce,
            quota=member_count,
            shim_url=f"{opts.shim_public_addr.rstrip('/')}/kbs/v0",
            resource_paths=written,
        )

    async def teardown(self, opts: ConfidentialScalingGroupOpts, session_id: uuid.UUID) -> int:
        target = BrokerTarget.of(opts)
        async with self._db.begin_readonly_session() as db_session:
            rows = list(
                (
                    await db_session.scalars(
                        sa.select(ConfidentialSessionResourceRow).where(
                            (ConfidentialSessionResourceRow.session_id == session_id)
                            & (ConfidentialSessionResourceRow.deleted_at.is_(None))
                        )
                    )
                ).all()
            )
        destroyed = 0
        for row in rows:
            await self._broker.destroy_resource(target, row.resource_path)
            async with self._db.begin_session() as db_session:
                await db_session.execute(
                    sa.update(ConfidentialSessionResourceRow)
                    .where(ConfidentialSessionResourceRow.id == row.id)
                    .values(deleted_at=datetime.now(UTC))
                )
            destroyed += 1
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                sa.delete(ConfidentialNonceRow).where(ConfidentialNonceRow.session_id == session_id)
            )
        return destroyed

    async def reconcile(self, endpoints: Mapping[str, ConfidentialScalingGroupOpts]) -> int:
        async with self._db.begin_readonly_session() as db_session:
            live = sa.select(SessionRow.id).where(SessionRow.status.not_in(DEAD_SESSION_STATUSES))
            orphans = list(
                (
                    await db_session.scalars(
                        sa.select(ConfidentialSessionResourceRow).where(
                            ConfidentialSessionResourceRow.deleted_at.is_(None)
                            & ConfidentialSessionResourceRow.session_id.not_in(live)
                        )
                    )
                ).all()
            )
        swept = 0
        for row in orphans:
            opts = endpoints.get(row.endpoint)
            if opts is None:
                continue
            try:
                await self._broker.destroy_resource(BrokerTarget.of(opts), row.resource_path)
            except BrokerUnreachable:
                continue
            async with self._db.begin_session() as db_session:
                await db_session.execute(
                    sa.update(ConfidentialSessionResourceRow)
                    .where(ConfidentialSessionResourceRow.id == row.id)
                    .values(deleted_at=datetime.now(UTC))
                )
                await db_session.execute(
                    sa.delete(ConfidentialNonceRow).where(
                        ConfidentialNonceRow.session_id == row.session_id
                    )
                )
            swept += 1
        ConfidentialMetricObserver.instance().observe_orphans_swept(swept)
        return swept
