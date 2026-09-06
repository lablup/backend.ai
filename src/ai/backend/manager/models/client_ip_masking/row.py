from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.manager.data.client_ip.masking import (
    MAX_IPV4_PREFIX,
    MAX_IPV6_PREFIX,
    ClientIPMaskingMode,
    ClientIPMaskingTarget,
)
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("ClientIPMaskingPolicyRow",)


class ClientIPMaskingPolicyRow(LifecycleTimestampsMixin, Base):
    """The masking a recorded client IP gets, one row per target.

    A target with no row falls back to the ``default`` row, and no ``default`` row
    means the address is recorded as observed.
    """

    __tablename__ = "client_ip_masking_policies"

    __table_args__ = (
        sa.UniqueConstraint("target_type", name="uq_client_ip_masking_policies_target_type"),
        sa.CheckConstraint(
            f"ipv4_prefix IS NULL OR (ipv4_prefix BETWEEN 0 AND {MAX_IPV4_PREFIX})",
            name="ck_client_ip_masking_policies_ipv4_prefix",
        ),
        sa.CheckConstraint(
            f"ipv6_prefix IS NULL OR (ipv6_prefix BETWEEN 0 AND {MAX_IPV6_PREFIX})",
            name="ck_client_ip_masking_policies_ipv6_prefix",
        ),
    )

    id: Mapped[ClientIPMaskingPolicyID] = mapped_column(
        "id",
        GUID(ClientIPMaskingPolicyID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    target_type: Mapped[ClientIPMaskingTarget] = mapped_column(
        "target_type", StrEnumType(ClientIPMaskingTarget), nullable=False
    )
    mode: Mapped[ClientIPMaskingMode] = mapped_column(
        "mode", StrEnumType(ClientIPMaskingMode), nullable=False
    )
    # How much of the address ``truncate`` leaves. NULL takes the built-in width.
    ipv4_prefix: Mapped[int | None] = mapped_column("ipv4_prefix", sa.SmallInteger, nullable=True)
    ipv6_prefix: Mapped[int | None] = mapped_column("ipv6_prefix", sa.SmallInteger, nullable=True)

    def to_data(self) -> ClientIPMaskingPolicyData:
        return ClientIPMaskingPolicyData(
            id=self.id,
            target_type=self.target_type,
            mode=self.mode,
            ipv4_prefix=self.ipv4_prefix,
            ipv6_prefix=self.ipv6_prefix,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
