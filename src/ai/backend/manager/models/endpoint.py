import sqlalchemy as sa

from .base import Base, EndpointIdColumn, ResourceSlotColumn

__all__ = ("EndpointRow",)


class EndpointRow(Base):
    __tablename__ = "endpoints"

    id = EndpointIdColumn()
    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    traffic_ratio = sa.Column("traffic_ratio", sa.Float, nullable=False)
    url = sa.Column("url", sa.String(length=1024), nullable=False)

    image = sa.Column("image", sa.ForeignKey("images.id", ondelete="RESTRICT"), nullable=False)
    model = sa.Column("model", sa.ForeignKey("vfolders.id", ondelete="RESTRICT"), nullable=False)
    project = sa.Column(
        "project", sa.ForeignKey("domains.name", ondelete="RESTRICT"), nullable=False
    )
    resource_group = sa.Column(
        "resource_group", sa.ForeignKey("scaling_groups.name", ondelete="RESTRICT"), nullable=False
    )
