import sqlalchemy as sa

from .base import GUID, Base, IDColumn

__all__ = ("RoutingRow",)


class RoutingRow(Base):
    __tablename__ = "routings"

    id = IDColumn("id")
    session = sa.Column(
        "session", GUID, sa.ForeignKey("sessions.id", ondelete="RESTRICT"), nullable=False
    )

    traffic_ratio = sa.Column("traffic_ratio", sa.Float(), nullable=False)
