import sqlalchemy as sa

from .base import GUID, Base, IDColumn

__all__ = ("RoutingRow",)


class RoutingRow(Base):
    __tablename__ = "routings"
    __table_args__ = (
        sa.UniqueConstraint("endpoint", "session", name="uq_routings_endpoint_session"),
    )

    id = IDColumn("id")
    endpoint = sa.Column(
        "endpoint", GUID, sa.ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=False
    )
    session = sa.Column(
        "session", GUID, sa.ForeignKey("sessions.id", ondelete="RESTRICT"), nullable=False
    )

    traffic_ratio = sa.Column("traffic_ratio", sa.Float(), nullable=False)
