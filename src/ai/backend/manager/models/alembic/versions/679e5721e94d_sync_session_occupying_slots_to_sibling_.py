"""sync_session_occupying_slots_to_sibling_kernels

Revision ID: 679e5721e94d
Revises: f56a82d0ac9f
Create Date: 2024-04-01 17:34:33.480996

"""

import textwrap
from typing import Any, cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Session, load_only, registry, relationship, selectinload
from sqlalchemy.sql import text

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.base import GUID, IDColumn, ResourceSlotColumn, convention

# revision identifiers, used by Alembic.
revision = "679e5721e94d"
down_revision = "f56a82d0ac9f"
branch_labels = None
depends_on = None

metadata = sa.MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()

PAGE_SIZE = 100


class SessionRow(Base):
    __tablename__ = "sessions"
    __table_args__ = {"extend_existing": True}

    id = IDColumn()
    cluster_size = sa.Column("cluster_size", sa.Integer, nullable=False, default=1)
    starts_at = sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True, default=sa.null())
    status_history = sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null())
    occupying_slots = sa.Column("occupying_slots", ResourceSlotColumn(), nullable=False)

    kernels = relationship("KernelRow")


class KernelRow(Base):
    __tablename__ = "kernels"
    __table_args__ = {"extend_existing": True}

    id = IDColumn()
    session_id = sa.Column(
        "session_id",
        GUID,
        sa.ForeignKey("sessions.id"),
        unique=False,
        index=True,
        nullable=False,
    )
    occupied_slots = sa.Column("occupied_slots", ResourceSlotColumn(), nullable=False)


def _sync_single_kernel_cluster_session():
    conn = op.get_bind()
    sync_stmt = textwrap.dedent(
        """
        UPDATE sessions
        SET occupying_slots = kernels.occupied_slots
        FROM kernels
        WHERE sessions.id = kernels.session_id
        AND sessions.cluster_size = 1;
        """
    )
    conn.execute(text(sync_stmt))


def _sync_multi_kernel_cluster_session():
    db_sess = Session(op.get_bind())

    while True:
        select_stmt = (
            sa.select(SessionRow)
            .where(
                (SessionRow.cluster_size != 1)
                & (SessionRow.occupying_slots == {})
                & (SessionRow.status_history.op("?")("RUNNING"))
            )
            .limit(PAGE_SIZE)
            .options(selectinload(SessionRow.kernels).options(load_only(KernelRow.occupied_slots)))
        )
        session_list = cast(list[SessionRow], db_sess.scalars(select_stmt).all())
        if not session_list:
            return

        update_stmt = (
            sa.update(SessionRow)
            .where(SessionRow.id == sa.bindparam("session_id"))
            .values(occupying_slots=sa.bindparam("occupying_slots"))
        )
        data = []
        for session in session_list:
            occupying_slots = sum([k.occupied_slots for k in session.kernels], start=ResourceSlot())
            data.append({"session_id": session.id, "occupying_slots": occupying_slots})
        db_sess.execute(update_stmt, data)


def upgrade():
    _sync_single_kernel_cluster_session()
    _sync_multi_kernel_cluster_session()


def downgrade():
    pass
