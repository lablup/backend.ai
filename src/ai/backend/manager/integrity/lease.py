from __future__ import annotations

import enum
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Final, override

import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

DEFAULT_TERM: Final = timedelta(minutes=30)
FENCE_GRACE: Final = timedelta(minutes=5)

EXCLUSIVITY_DISCLOSURE: Final = (
    "An integrity-tier folder carries one active mount at a time. A second session is refused"
    " while the lease is held, and a lease whose holder is only believed dead is reclaimed by a"
    " recorded operator action rather than automatically."
)


class LeaseFence(enum.StrEnum):
    HELD = "held"
    RELEASED = "released"
    ELAPSED = "elapsed"
    BROKEN = "broken"


class MountLeaseHeld(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/integrity-mount-lease-held"
    error_title = "The integrity-tier folder is already mounted by another session."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.CONFLICT,
        )


class MountLeaseUnfenced(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/integrity-mount-lease-unfenced"
    error_title = "The integrity-tier folder's lease cannot be reclaimed without positive fencing."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.CONFLICT,
        )


class IntegrityMountLeaseRow(Base):  # type: ignore[misc]
    __tablename__ = "integrity_mount_leases"
    folder_id: Mapped[uuid.UUID] = mapped_column("folder_id", GUID, primary_key=True)
    holder: Mapped[uuid.UUID | None] = mapped_column("holder", GUID, nullable=True)
    epoch: Mapped[int] = mapped_column("epoch", sa.BigInteger, nullable=False, default=0)
    granted_at: Mapped[datetime | None] = mapped_column(
        "granted_at", sa.DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        "expires_at", sa.DateTime(timezone=True), nullable=True
    )
    fence: Mapped[LeaseFence] = mapped_column(
        "fence", StrEnumType(LeaseFence), nullable=False, default=LeaseFence.RELEASED
    )
    fence_reason: Mapped[str | None] = mapped_column("fence_reason", sa.Text, nullable=True)


@dataclass(frozen=True)
class MountLease:
    folder_id: uuid.UUID
    holder: uuid.UUID
    epoch: int
    expires_at: datetime

    def document(self) -> bytes:
        return json.dumps(
            {
                "folder": str(self.folder_id),
                "holder": str(self.holder),
                "epoch": self.epoch,
                "expires_at": int(self.expires_at.timestamp()),
                "exclusivity": EXCLUSIVITY_DISCLOSURE,
            },
            sort_keys=True,
        ).encode()


def _fenced() -> sa.sql.elements.ColumnElement[bool]:
    row = IntegrityMountLeaseRow
    return sa.or_(row.holder.is_(None), row.fence != LeaseFence.HELD)


class MountLeases:
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def acquire(
        self, folder_id: uuid.UUID, holder: uuid.UUID, term: timedelta = DEFAULT_TERM
    ) -> MountLease:
        now = datetime.now(UTC)
        expires_at = now + term
        row = IntegrityMountLeaseRow
        async with self._db.begin() as conn:
            await conn.execute(
                pg_insert(row)
                .values(folder_id=folder_id, epoch=0, fence=LeaseFence.RELEASED)
                .on_conflict_do_nothing(index_elements=[row.folder_id])
            )
            taken = (
                await conn.execute(
                    sa.update(row)
                    .where(sa.and_(row.folder_id == folder_id, _fenced()))
                    .values(
                        holder=holder,
                        epoch=row.epoch + 1,
                        granted_at=now,
                        expires_at=expires_at,
                        fence=LeaseFence.HELD,
                        fence_reason=None,
                    )
                    .returning(row.epoch)
                )
            ).scalar()
            if taken is None:
                held = (
                    await conn.execute(sa.select(row.holder).where(row.folder_id == folder_id))
                ).scalar()
                raise MountLeaseHeld(
                    f"the integrity-tier folder {folder_id} is mounted by session {held}"
                )
        return MountLease(folder_id, holder, taken, expires_at)

    async def renew(
        self, folder_id: uuid.UUID, holder: uuid.UUID, term: timedelta = DEFAULT_TERM
    ) -> MountLease:
        now = datetime.now(UTC)
        expires_at = now + term
        row = IntegrityMountLeaseRow
        async with self._db.begin() as conn:
            renewed = (
                await conn.execute(
                    sa.update(row)
                    .where(
                        sa.and_(
                            row.folder_id == folder_id,
                            row.holder == holder,
                            row.fence == LeaseFence.HELD,
                        )
                    )
                    .values(expires_at=expires_at)
                    .returning(row.epoch)
                )
            ).scalar()
        if renewed is None:
            raise MountLeaseHeld(f"session {holder} no longer holds the lease on {folder_id}")
        return MountLease(folder_id, holder, renewed, expires_at)

    async def release(self, folder_id: uuid.UUID, holder: uuid.UUID, confirmation: str) -> None:
        row = IntegrityMountLeaseRow
        async with self._db.begin() as conn:
            await conn.execute(
                sa.update(row)
                .where(sa.and_(row.folder_id == folder_id, row.holder == holder))
                .values(fence=LeaseFence.RELEASED, fence_reason=confirmation, expires_at=None)
            )

    async def reclaim(self, folder_id: uuid.UUID) -> None:
        now = datetime.now(UTC)
        row = IntegrityMountLeaseRow
        async with self._db.begin() as conn:
            fenced = (
                await conn.execute(
                    sa.update(row)
                    .where(
                        sa.and_(
                            row.folder_id == folder_id,
                            row.fence == LeaseFence.HELD,
                            row.expires_at < now - FENCE_GRACE,
                        )
                    )
                    .values(
                        fence=LeaseFence.ELAPSED,
                        fence_reason="the attested guest-side lease term elapsed",
                    )
                    .returning(row.epoch)
                )
            ).scalar()
        if fenced is None:
            raise MountLeaseUnfenced(
                f"the lease on {folder_id} is live or its holder is only believed dead;"
                " reclaim it with a recorded operator action instead"
            )

    async def break_lease(self, folder_id: uuid.UUID, operator: str, reason: str) -> None:
        row = IntegrityMountLeaseRow
        async with self._db.begin() as conn:
            await conn.execute(
                sa.update(row)
                .where(row.folder_id == folder_id)
                .values(fence=LeaseFence.BROKEN, fence_reason=f"{operator}: {reason}")
            )

    async def held_by(self, folder_id: uuid.UUID) -> MountLease | None:
        row = IntegrityMountLeaseRow
        async with self._db.begin_readonly() as conn:
            found = (
                await conn.execute(
                    sa.select(row.holder, row.epoch, row.expires_at).where(
                        sa.and_(row.folder_id == folder_id, row.fence == LeaseFence.HELD)
                    )
                )
            ).first()
        if found is None or found.holder is None:
            return None
        return MountLease(folder_id, found.holder, found.epoch, found.expires_at)
