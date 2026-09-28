from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from sqlalchemy.sql.expression import SQLColumnExpression

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.association_container_registries_groups.row import (
        AssociationContainerRegistriesGroupsRow,
    )

__all__: Sequence[str] = ("ContainerRegistryRow",)


# Join condition for the relationship below, which only the legacy RBAC path reads.
# Delete both together.
def _get_association_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.association_container_registries_groups.row import (
        AssociationContainerRegistriesGroupsRow,
    )

    return ContainerRegistryRow.id == foreign(AssociationContainerRegistriesGroupsRow.registry_id)


class ContainerRegistryRow(Base):
    __tablename__ = "container_registries"

    id: Mapped[ContainerRegistryID] = mapped_column(
        "id",
        GUID(ContainerRegistryID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    url: Mapped[str] = mapped_column("url", sa.String(length=512), index=True, nullable=False)
    registry_name: Mapped[str] = mapped_column(
        "registry_name", sa.String(length=255), index=True, nullable=False
    )
    type: Mapped[ContainerRegistryType] = mapped_column(
        "type",
        StrEnumType(ContainerRegistryType),
        default=ContainerRegistryType.DOCKER,
        server_default=ContainerRegistryType.DOCKER,
        nullable=False,
        index=True,
    )
    project: Mapped[str | None] = mapped_column(
        "project", sa.String(length=255), index=True, nullable=True
    )
    username: Mapped[str | None] = mapped_column("username", sa.String(length=255), nullable=True)
    password: Mapped[str | None] = mapped_column("password", sa.String, nullable=True)
    ssl_verify: Mapped[bool | None] = mapped_column(
        "ssl_verify", sa.Boolean, nullable=True, server_default=sa.text("true"), index=True
    )
    is_global: Mapped[bool] = mapped_column(
        "is_global", sa.Boolean, nullable=False, server_default=sa.text("true"), index=True
    )
    extra: Mapped[dict[str, Any] | None] = mapped_column(
        "extra", sa.JSON, nullable=True, default=None
    )

    # Used only by the legacy RBAC path (ImagePermissionContextBuilder in
    # models/image/row.py). Delete it together with models/rbac.
    association_container_registries_groups_rows: Mapped[
        list[AssociationContainerRegistriesGroupsRow]
    ] = relationship(
        "AssociationContainerRegistriesGroupsRow",
        primaryjoin=_get_association_join_condition,
    )

    def __init__(
        self,
        id: ContainerRegistryID,
        url: str,
        registry_name: str,
        type: ContainerRegistryType,
        project: str | None = None,
        username: str | None = None,
        password: str | None = None,
        ssl_verify: bool | None = None,
        is_global: bool = True,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.id = id
        self.url = url
        self.registry_name = registry_name
        self.type = type
        self.project = project
        self.username = username
        self.password = password
        self.ssl_verify = ssl_verify
        self.is_global = is_global
        self.extra = extra

    # Used only by gql_legacy (load_by_hostname and DeleteContainerRegistry in
    # api/gql_legacy/container_registry.py). Replace it with repository.get_by_registry_name
    # together with gql_legacy.
    @classmethod
    async def list_by_registry_name(
        cls,
        session: AsyncSession,
        registry_name: str,
    ) -> Sequence[ContainerRegistryRow]:
        query = sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.registry_name == registry_name
        )
        result = await session.execute(query)
        rows = result.scalars().all()
        if not rows:
            raise NoResultFound
        return rows

    @classmethod
    def scope_id_expr(cls) -> SQLColumnExpression[ContainerRegistryID]:
        return cls.id

    @classmethod
    def scope_name_expr(cls) -> SQLColumnExpression[str]:
        return cls.registry_name
