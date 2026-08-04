from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from typing import Final

import aiohttp
import sqlalchemy as sa
from yarl import URL

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.confidential.blobs import MeasuredBlobStore
from ai.backend.manager.confidential.broker import BrokerClient
from ai.backend.manager.confidential.policy import ReleasePolicyComposer
from ai.backend.manager.confidential.provisioning import (
    RECONCILE_INTERVAL,
    SessionResourceProvisioner,
)
from ai.backend.manager.confidential.references import ReferenceValueStore
from ai.backend.manager.confidential.shim import AuthorisationShim
from ai.backend.manager.confidential.storage import FolderKeyCustodian
from ai.backend.manager.errors.confidential import ConfidentialCapabilityRefused
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.models.scaling_group.types import ConfidentialScalingGroupOpts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

RECONCILER_LOCK_KEY: Final = 7318541269834011


def _is_local(host: str) -> bool:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        try:
            address = ipaddress.ip_address(socket.gethostbyname(host))
        except (OSError, ValueError):
            return host in ("localhost", "")
    return address.is_loopback or address.is_unspecified or address.is_link_local


async def verify_capability(opts: ConfidentialScalingGroupOpts) -> None:
    if not opts.enabled:
        return
    if opts.insecure_development:
        log.warning(
            "confidential: {} runs under the insecure-development escape hatch;"
            " the confidential label is disabled end to end",
            opts.broker_endpoint,
        )
        return
    url = URL(opts.broker_endpoint)
    if not url.host or _is_local(url.host):
        raise ConfidentialCapabilityRefused(
            extra_msg=f"broker endpoint {opts.broker_endpoint} resolves to a manager-local address"
        )
    if not opts.broker_admin_token:
        raise ConfidentialCapabilityRefused(
            extra_msg="the broker reports an unauthenticated administrative mode"
        )
    if not opts.provisioning_record:
        raise ConfidentialCapabilityRefused(
            extra_msg="confidential capability requires a signed broker provisioning record"
        )


class ConfidentialPlane:
    def __init__(self, db: ExtendedAsyncSAEngine, session: aiohttp.ClientSession) -> None:
        self._db = db
        self._session = session
        self.broker = BrokerClient(session)
        self.shim = AuthorisationShim(db, self.broker)
        self.references = ReferenceValueStore(db, self.shim)
        self.policy = ReleasePolicyComposer(db, self.broker, self.references)
        self.provisioner = SessionResourceProvisioner(db, self.broker, self.shim)
        self.blobs = MeasuredBlobStore(db)
        self.custodian = FolderKeyCustodian(self.broker)
        self._reconciler: asyncio.Task[None] | None = None

    async def opts_of(self, scaling_group: str) -> ConfidentialScalingGroupOpts:
        async with self._db.begin_readonly_session() as db_session:
            row = await db_session.get(ScalingGroupRow, scaling_group)
        if row is None:
            raise ConfidentialCapabilityRefused(extra_msg=f"unknown scaling group {scaling_group}")
        if not row.confidential.enabled:
            raise ConfidentialCapabilityRefused(
                extra_msg=f"scaling group {scaling_group} is not confidential"
            )
        return row.confidential

    async def confidential_endpoints(self) -> dict[str, ConfidentialScalingGroupOpts]:
        async with self._db.begin_readonly_session() as db_session:
            rows = await db_session.scalars(sa.select(ScalingGroupRow))
            return {
                row.confidential.broker_endpoint: row.confidential
                for row in rows.all()
                if row.confidential.enabled and row.confidential.broker_endpoint
            }

    async def _reconcile_forever(self) -> None:
        while True:
            await asyncio.sleep(RECONCILE_INTERVAL)
            try:
                async with self._db.connect() as conn:
                    acquired = await conn.exec_driver_sql(
                        f"SELECT pg_try_advisory_lock({RECONCILER_LOCK_KEY:d});"
                    )
                    if not acquired.scalar():
                        continue
                    try:
                        await self.provisioner.reconcile(await self.confidential_endpoints())
                    finally:
                        await conn.exec_driver_sql(
                            f"SELECT pg_advisory_unlock({RECONCILER_LOCK_KEY:d});"
                        )
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("confidential: orphan reconciliation pass failed")

    def start(self) -> None:
        if self._reconciler is None:
            self._reconciler = asyncio.create_task(self._reconcile_forever())
            self._reconciler.set_name("confidential_orphan_reconciler")

    async def close(self) -> None:
        if self._reconciler is not None:
            self._reconciler.cancel()
            try:
                await self._reconciler
            except asyncio.CancelledError:
                pass
            self._reconciler = None
        await self._session.close()
