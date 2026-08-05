from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, Final

import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.confidential.broker import BrokerClient, BrokerTarget
from ai.backend.manager.confidential.references import ReferenceValueStore
from ai.backend.manager.errors.confidential import BrokerUnreachable
from ai.backend.manager.metrics.confidential import ConfidentialMetricObserver
from ai.backend.manager.models.confidential.row import (
    ConfidentialPolicyJournalRow,
    ConfidentialReferenceValueRow,
    ConfidentialTcbGraceRow,
)
from ai.backend.manager.models.scaling_group.types import ConfidentialScalingGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

CPU_BODY: Final = 'input.submods.cpu0["ear.veraison.annotated-evidence"].tdx.quote.body'
CPU_STATUS: Final = 'input.submods.cpu0["ear.status"]'
GPU_EVIDENCE: Final = 'input.submods.gpu0["ear.veraison.annotated-evidence"].nvidia'
CPU_MEASUREMENT_FIELDS: Final = ("mr_td", "rtmr_1", "rtmr_2", "mr_config_id")
RVPS_FIELDS: Final = ("mr_td", "rtmr_1", "rtmr_2", "xfam", "tdvfkernel", "tdvfkernelparams")


def endpoint_lock_key(endpoint: str) -> int:
    return int.from_bytes(hashlib.sha256(endpoint.encode("utf-8")).digest()[:8], "big") >> 1


def _rule(measurements: dict[str, Any], statuses: tuple[str, ...]) -> str:
    if len(statuses) == 1:
        lines = [f'    {CPU_STATUS} == "{statuses[0]}"']
    else:
        allowed = ", ".join(f'"{status}"' for status in statuses)
        lines = [f"    {CPU_STATUS} in {{{allowed}}}"]
    lines.append(f"    body := {CPU_BODY}")
    for field in CPU_MEASUREMENT_FIELDS:
        value = measurements.get(field)
        if isinstance(value, list):
            if value:
                admitted = ", ".join(json.dumps(entry) for entry in value)
                lines.append(f"    body.{field} in {{{admitted}}}")
        elif value:
            lines.append(f'    body.{field} == "{value}"')
    gpu = measurements.get("gpu")
    if isinstance(gpu, dict) and gpu:
        lines.append('    input.submods.gpu0["ear.status"] == "affirming"')
        lines.append(f"    gpu := {GPU_EVIDENCE}")
        for key in sorted(gpu):
            value = gpu[key]
            rendered = json.dumps(value) if not isinstance(value, str) else f'"{value}"'
            lines.append(f'    gpu["{key}"] == {rendered}')
    body = "\n".join(lines)
    return f"allow if {{\n{body}\n}}"


def reference_payload(rows: list[ConfidentialReferenceValueRow]) -> bytes:
    values: dict[str, list[Any]] = {field: [] for field in RVPS_FIELDS}
    for row in rows:
        for field in RVPS_FIELDS:
            value = row.measurements.get(field)
            for entry in value if isinstance(value, list) else [value]:
                if entry and entry not in values[field]:
                    values[field].append(entry)
    return json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ReleasePolicyComposer:
    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        broker: BrokerClient,
        references: ReferenceValueStore,
    ) -> None:
        self._db = db
        self._broker = broker
        self._references = references

    @asynccontextmanager
    async def _endpoint_lock(self, endpoint: str) -> AsyncIterator[None]:
        key = endpoint_lock_key(endpoint)
        async with self._db.connect() as conn:
            await conn.exec_driver_sql(f"SELECT pg_advisory_lock({key:d});")
            try:
                yield
            finally:
                await conn.exec_driver_sql(f"SELECT pg_advisory_unlock({key:d});")

    async def grace(self, endpoint: str) -> ConfidentialTcbGraceRow | None:
        async with self._db.begin_readonly_session() as db_session:
            row = await db_session.get(ConfidentialTcbGraceRow, endpoint)
            if row is None or row.resolved_at is not None:
                return None
            return row

    async def open_grace(
        self, opts: ConfidentialScalingGroupOpts, platform_status: str, disclosure: str
    ) -> ConfidentialTcbGraceRow:
        now = datetime.now(UTC)
        async with self._db.begin_session() as db_session:
            row = await db_session.get(ConfidentialTcbGraceRow, opts.broker_endpoint)
            if row is None:
                row = ConfidentialTcbGraceRow(endpoint=opts.broker_endpoint)
                db_session.add(row)
            row.platform_status = platform_status
            row.started_at = now
            row.expires_at = now + opts.tcb_grace_period
            row.disclosure = disclosure
            row.resolved_at = None
            await db_session.flush()
        log.warning(
            "confidential: trusted-computing-base grace window open on {} until {} ({})",
            opts.broker_endpoint,
            row.expires_at,
            platform_status,
        )
        ConfidentialMetricObserver.instance().observe_tcb_grace(opts.broker_endpoint, True)
        return row

    async def enforce_grace_expiry(self, opts: ConfidentialScalingGroupOpts) -> bool:
        endpoint = opts.broker_endpoint
        async with self._db.begin_readonly_session() as db_session:
            row = await db_session.get(ConfidentialTcbGraceRow, endpoint)
            if row is None or row.resolved_at is not None or row.expires_at > datetime.now(UTC):
                return False
            last_upload = await db_session.scalar(
                sa.select(sa.func.max(ConfidentialPolicyJournalRow.uploaded_at)).where(
                    ConfidentialPolicyJournalRow.endpoint == endpoint
                )
            )
        if last_upload is not None and last_upload >= row.expires_at:
            return False
        await self.compose_and_upload(opts)
        log.warning(
            "confidential: trusted-computing-base grace window on {} expired at {};"
            " a hard-deny release policy is now uploaded",
            endpoint,
            row.expires_at,
        )
        return True

    async def close_grace(self, endpoint: str) -> None:
        async with self._db.begin_session() as db_session:
            row = await db_session.get(ConfidentialTcbGraceRow, endpoint)
            if row is not None:
                row.resolved_at = datetime.now(UTC)
        ConfidentialMetricObserver.instance().observe_tcb_grace(endpoint, False)

    async def render(self, endpoint: str) -> str:
        for value_id, value_endpoint, missing in await self._references.invalidate_unpinned():
            log.warning(
                "confidential: stored reference value {} on {} leaves {} unpinned;"
                " it is marked invalid and contributes no rule to any composed release policy",
                value_id,
                value_endpoint,
                ", ".join(missing),
            )
        await self._references.close_expired_windows(endpoint)
        grace = await self.grace(endpoint)
        hard_denied = grace is not None and grace.expires_at <= datetime.now(UTC)
        statuses = ("affirming",) if grace is None else ("affirming", "warning")
        rules = (
            []
            if hard_denied
            else [
                _rule(row.measurements, statuses)
                for row in await self._references.admissible(endpoint)
            ]
        )
        return "\n\n".join(["package policy", "import rego.v1", "default allow = false", *rules])

    async def compose_and_upload(self, opts: ConfidentialScalingGroupOpts) -> str:
        endpoint = opts.broker_endpoint
        observer = ConfidentialMetricObserver.instance()
        async with self._endpoint_lock(endpoint):
            document = await self.render(endpoint)
            content_hash = hashlib.sha384(document.encode("utf-8")).hexdigest()
            async with self._db.begin_session() as db_session:
                journal = ConfidentialPolicyJournalRow(
                    endpoint=endpoint, content_hash=content_hash, document=document
                )
                db_session.add(journal)
                await db_session.flush()
                journal_id = journal.id
            try:
                await self._broker.register_reference_value(
                    BrokerTarget.of(opts),
                    reference_payload(await self._references.admissible(endpoint)),
                )
                await self._broker.upload_release_policy(BrokerTarget.of(opts), document)
            except BrokerUnreachable as e:
                async with self._db.begin_session() as db_session:
                    await db_session.execute(
                        sa.update(ConfidentialPolicyJournalRow)
                        .where(ConfidentialPolicyJournalRow.id == journal_id)
                        .values(upload_failure=str(e))
                    )
                observer.observe_policy_upload("unreachable")
                raise
            async with self._db.begin_session() as db_session:
                await db_session.execute(
                    sa.update(ConfidentialPolicyJournalRow)
                    .where(ConfidentialPolicyJournalRow.id == journal_id)
                    .values(uploaded_at=datetime.now(UTC))
                )
            observer.observe_policy_upload("uploaded")
            return content_hash
