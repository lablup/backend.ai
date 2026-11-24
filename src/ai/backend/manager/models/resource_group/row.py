from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable, Sequence
from typing import (
    Any,
)

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from sqlalchemy.sql.expression import SQLColumnExpression, false, true

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.data.deployment.types import DeploymentOptions
from ai.backend.manager.data.resource_group.types import FairShareResourceGroupSpec
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.models.base import (
    GUID,
    Base,
    PydanticColumn,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.types import QueryCondition
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__: Sequence[str] = ("ResourceGroupRow",)


# When scheduling, we take the union of allowed scaling groups for
# each domain, group, and keypair.


class ResourceGroupForDomainRow(Base):
    __tablename__ = "sgroups_for_domains"
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        sa.ForeignKey("scaling_groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    domain_id: Mapped[DomainID] = mapped_column(
        "domain_id",
        sa.ForeignKey("domains.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("resource_group_id", "domain_id", name="uq_sgroup_domain"),
    )


# For compatibility
sgroups_for_domains = ResourceGroupForDomainRow.__table__


class ResourceGroupForProjectRow(Base):
    __tablename__ = "sgroups_for_groups"
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        sa.ForeignKey("scaling_groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    group: Mapped[uuid.UUID] = mapped_column(
        "group",
        sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    __table_args__ = (
        # constraint
        sa.UniqueConstraint("resource_group_id", "group", name="uq_sgroup_ugroup"),
    )


# For compatibility. In src, only gql_legacy (scaling_group.py) uses it.
# Delete it with the gql_legacy cleanup.
sgroups_for_groups = ResourceGroupForProjectRow.__table__


class ResourceGroupForKeypairsRow(Base):
    __tablename__ = "sgroups_for_keypairs"
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        sa.ForeignKey("scaling_groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    access_key: Mapped[str] = mapped_column(
        "access_key",
        sa.ForeignKey("keypairs.access_key", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("resource_group_id", "access_key", name="uq_sgroup_akey"),
    )


# For compatibility. In src, only gql_legacy (scaling_group.py) uses it.
# Delete it with the gql_legacy cleanup.
sgroups_for_keypairs = ResourceGroupForKeypairsRow.__table__


class ResourceGroupRow(CreatedAtMixin, Base):
    # The table keeps its original name; the rename stopped at the Python identifiers.
    __tablename__ = "scaling_groups"
    __table_args__ = (
        # Partial unique index: at most one row may have is_default = true.
        sa.Index(
            "uq_scaling_groups_is_default",
            "is_default",
            unique=True,
            postgresql_where=sa.text("is_default"),
        ),
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=64), primary_key=True)
    id: Mapped[ResourceGroupID] = mapped_column(
        "id",
        GUID(ResourceGroupID),
        nullable=False,
        unique=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    description: Mapped[str | None] = mapped_column("description", sa.String(length=512))
    is_active: Mapped[bool | None] = mapped_column(
        "is_active", sa.Boolean, index=True, default=True
    )
    is_public: Mapped[bool] = mapped_column(
        "is_public", sa.Boolean, index=True, default=True, server_default=true(), nullable=False
    )
    # At most one scaling group may be the default at a time. This is enforced by
    # the partial unique index in ``__table_args__`` (a minimum of one is NOT
    # guaranteed). To switch the default, clear the previous default before
    # setting the new one within the same transaction.
    is_default: Mapped[bool] = mapped_column(
        "is_default", sa.Boolean, default=False, server_default=false(), nullable=False
    )
    wsproxy_addr: Mapped[str | None] = mapped_column(
        "wsproxy_addr", sa.String(length=1024), nullable=True
    )
    wsproxy_api_token: Mapped[str | None] = mapped_column(
        "wsproxy_api_token", sa.String(length=128), nullable=True
    )
    driver: Mapped[str] = mapped_column("driver", sa.String(length=64), nullable=False)
    driver_opts: Mapped[dict[str, Any]] = mapped_column(
        "driver_opts", pgsql.JSONB(), nullable=False, default={}
    )
    scheduler: Mapped[str] = mapped_column("scheduler", sa.String(length=64), nullable=False)
    use_host_network: Mapped[bool] = mapped_column(
        "use_host_network", sa.Boolean, nullable=False, default=False
    )
    scheduler_opts: Mapped[ResourceGroupOpts] = mapped_column(
        "scheduler_opts",
        PydanticColumn(ResourceGroupOpts),
        nullable=False,
        default=ResourceGroupOpts,
    )
    fair_share_spec: Mapped[FairShareResourceGroupSpec | None] = mapped_column(
        "fair_share_spec",
        PydanticColumn(FairShareResourceGroupSpec),
        nullable=True,
        default=None,
    )
    # Default operational options snapshot-copied onto each new
    # deployment in this scaling group. See :class:`DeploymentOptions`.
    default_deployment_options: Mapped[DeploymentOptions] = mapped_column(
        "default_deployment_options",
        PydanticColumn(DeploymentOptions),
        nullable=False,
        default=DeploymentOptions,
    )
    # Default session-side operational options used by the resolver
    # when a create-session request omits fields. See
    # :class:`DefaultSessionOptions`.
    default_session_options: Mapped[DefaultSessionOptions] = mapped_column(
        "default_session_options",
        PydanticColumn(DefaultSessionOptions),
        nullable=False,
        default=DefaultSessionOptions,
    )

    @classmethod
    def scope_id_expr(cls) -> SQLColumnExpression[ResourceGroupID]:
        return cls.id

    @classmethod
    def scope_name_expr(cls) -> SQLColumnExpression[str]:
        return cls.name

    # Called only by resolve_accessible_scaling_groups in api/gql_legacy/schema.py.
    # Delete it with gql_legacy.
    @classmethod
    async def list_by_condition(
        cls,
        conditions: Iterable[QueryCondition],
        *,
        db: ExtendedAsyncSAEngine,
    ) -> list[ResourceGroupRow]:
        stmt = sa.select(ResourceGroupRow)
        for cond in conditions:
            stmt = cond(stmt)
        async with db.begin_readonly_session() as db_session:
            return list((await db_session.scalars(stmt)).all())


# Builds the condition list_by_condition takes; api/gql_legacy/schema.py is the only
# caller. Delete it with gql_legacy.
def and_names(names: Iterable[str]) -> Callable[..., sa.sql.Select[Any]]:
    return lambda query_stmt: query_stmt.where(ResourceGroupRow.name.in_(names))


# For compatibility
resource_groups = ResourceGroupRow.__table__
