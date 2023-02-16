import sqlalchemy as sa
from sqlalchemy.orm import relationship

from .base import GUID, Base, EndpointIDColumn, ResourceSlotColumn

__all__ = ("EndpointRow",)


class EndpointRow(Base):
    __tablename__ = "endpoints"

    id = EndpointIDColumn()
    image = sa.Column(
        "image", GUID, sa.ForeignKey("images.id", ondelete="RESTRICT"), nullable=False
    )
    model = sa.Column(
        "model", GUID, sa.ForeignKey("vfolders.id", ondelete="RESTRICT"), nullable=False
    )
    project = sa.Column(
        "project",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="RESTRICT"),
        nullable=False,
    )
    resource_group = sa.Column(
        "resource_group",
        sa.ForeignKey("scaling_groups.name", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    url = sa.Column("url", sa.String(length=1024), nullable=False)

    routings = relationship("RoutingRow", back_populates="endpoint_row")
