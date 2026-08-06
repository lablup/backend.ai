from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.confidential.admission import check_admission_belt
from ai.backend.manager.confidential.broker import BrokerClient, BrokerTarget
from ai.backend.manager.confidential.launch import LaunchAuthority
from ai.backend.manager.confidential.payloads import TIME_RESOURCE, attested_time
from ai.backend.manager.confidential.shim import AuthorisationShim
from ai.backend.manager.errors.confidential import (
    BrokerRejected,
    BrokerUnreachable,
    ReleaseDenied,
)
from ai.backend.manager.metrics.confidential import ConfidentialMetricObserver
from ai.backend.manager.models.confidential.row import (
    ConfidentialGuestClaimRow,
    ConfidentialNonceRow,
    ConfidentialSessionResourceRow,
)
from ai.backend.manager.models.confidential.types import (
    DecisionActor,
    DecisionVerdict,
    SessionResourceKind,
)
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.scaling_group.types import (
    NONCE_RESIDUAL_DISCLOSURE,
    ConfidentialScalingGroupOpts,
)
from ai.backend.manager.models.session import DEAD_SESSION_STATUSES, SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

RECONCILE_INTERVAL: Final = 300.0
DRAIN_REASON: Final = "confidential-reference-value-drained"


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
        launch: LaunchAuthority,
    ) -> None:
        self._db = db
        self._broker = broker
        self._shim = shim
        self._launch = launch

    async def _settle(self, txn_func: Callable[[SASession], Awaitable[None]]) -> None:
        async with self._db.connect() as conn:
            await execute_with_txn_retry(txn_func, self._db.begin_session, conn)

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
        nonce = held or await self._launch.mint(
            opts,
            session_id=session_id,
            domain_name=domain_name,
            image_digest=image_digest,
            quota=member_count,
        )
        target = BrokerTarget.of(opts)
        await self._broker.put_resource(target, TIME_RESOURCE, attested_time())
        written: list[tuple[str, SessionResourceKind]] = []

        async def _record(db_session: SASession) -> None:
            for path, kind in written:
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
                    db_session=db_session,
                )
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
                )
            )

        try:
            for tag, (kind, payload) in resources.items():
                path = await self._shim.authorise_session_path(
                    domain_name, session_id, nonce, f"{domain_name}/{session_id}.{nonce}/{tag}"
                )
                await self._broker.put_resource(target, path, payload)
                written.append((path, kind))
        finally:
            if written:
                await self._settle(_record)
        return SessionProvisioning(
            session_id=session_id,
            nonce=nonce,
            quota=member_count,
            shim_url=f"{opts.shim_public_addr.rstrip('/')}/kbs/v0",
            resource_paths=[path for path, _ in written],
        )

    async def _destroy(
        self,
        endpoints: Mapping[str, ConfidentialScalingGroupOpts],
        row: ConfidentialSessionResourceRow,
    ) -> bool:
        opts = endpoints.get(row.endpoint)
        if opts is None:
            log.warning(
                "confidential: no configured broker at {} still holds {}, which survives",
                row.endpoint,
                row.resource_path,
            )
            return False
        try:
            await self._broker.destroy_resource(BrokerTarget.of(opts), row.resource_path)
        except (BrokerUnreachable, BrokerRejected, ReleaseDenied) as e:
            log.warning(
                "confidential: {} kept {}, which survives for the reconciler: {}",
                row.endpoint,
                row.resource_path,
                e,
            )
            return False
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                sa.update(ConfidentialSessionResourceRow)
                .where(ConfidentialSessionResourceRow.id == row.id)
                .values(deleted_at=datetime.now(UTC))
            )
        return True

    async def teardown(
        self, endpoints: Mapping[str, ConfidentialScalingGroupOpts], session_id: uuid.UUID
    ) -> int:
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
            if await self._destroy(endpoints, row):
                destroyed += 1

        async def _release(db_session: SASession) -> None:
            await db_session.execute(
                sa.delete(ConfidentialNonceRow).where(ConfidentialNonceRow.session_id == session_id)
            )
            await db_session.execute(
                sa.delete(ConfidentialGuestClaimRow).where(
                    ConfidentialGuestClaimRow.session_id == session_id
                )
            )

        await self._settle(_release)
        return destroyed

    async def disclose_drain(self, session_id: uuid.UUID, value_id: uuid.UUID) -> str:
        reason = f"{DRAIN_REASON}:{value_id}"
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                sa.update(SessionRow).where(SessionRow.id == session_id).values(status_info=reason)
            )
            await db_session.execute(
                sa.update(KernelRow)
                .where(KernelRow.session_id == session_id)
                .values(status_info=reason)
            )
            await self._shim.record(
                actor=DecisionActor.MANAGER,
                verdict=DecisionVerdict.DENIED,
                resource_path=DRAIN_REASON,
                failing_clause=(
                    f"reference value {value_id} was drained, so this session's confidential"
                    " resources were destroyed and every further guest fetch is refused"
                ),
                session_id=session_id,
                db_session=db_session,
            )
        log.warning(
            "confidential: session {} is stranded by the drain of reference value {}",
            session_id,
            value_id,
        )
        return reason

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
        stranded: set[uuid.UUID] = set()
        for row in orphans:
            if not await self._destroy(endpoints, row):
                continue
            stranded.add(row.session_id)
            swept += 1

        async def _release(db_session: SASession) -> None:
            await db_session.execute(
                sa.delete(ConfidentialNonceRow).where(ConfidentialNonceRow.session_id.in_(stranded))
            )

        if stranded:
            await self._settle(_release)
        ConfidentialMetricObserver.instance().observe_orphans_swept(swept)
        return swept
