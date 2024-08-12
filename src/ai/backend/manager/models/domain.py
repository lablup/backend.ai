from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, TypedDict

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.result import Result
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.orm import relationship

from ai.backend.common import msgpack
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.group import ProjectType

from ..defs import RESERVED_DOTFILES
from .base import (
    Base,
    ResourceSlotColumn,
    SlugType,
    VFolderHostPermissionColumn,
    batch_result,
    mapper_registry,
    set_if_set,
    simple_db_mutate,
    simple_db_mutate_returning_item,
)
from .scaling_group import ScalingGroup
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__: Sequence[str] = (
    "domains",
    "DomainRow",
    "Domain",
    "DomainInput",
    "ModifyDomainInput",
    "CreateDomain",
    "ModifyDomain",
    "DeleteDomain",
    "DomainDotfile",
    "MAXIMUM_DOTFILE_SIZE",
    "query_domain_dotfiles",
    "verify_dotfile_name",
)

MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB

domains = sa.Table(
    "domains",
    mapper_registry.metadata,
    sa.Column("name", SlugType(length=64, allow_unicode=True, allow_dot=True), primary_key=True),
    sa.Column("description", sa.String(length=512)),
    sa.Column("is_active", sa.Boolean, default=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    ),
    # TODO: separate resource-related fields with new domain resource policy table when needed.
    sa.Column("total_resource_slots", ResourceSlotColumn(), default="{}"),
    sa.Column(
        "allowed_vfolder_hosts",
        VFolderHostPermissionColumn(),
        nullable=False,
        default={},
    ),
    sa.Column("allowed_docker_registries", pgsql.ARRAY(sa.String), nullable=False, default="{}"),
    #: Field for synchronization with external services.
    sa.Column("integration_id", sa.String(length=512)),
    # dotfiles column, \x90 means empty list in msgpack
    sa.Column(
        "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
    ),
)


class DomainRow(Base):
    __table__ = domains
    sessions = relationship("SessionRow", back_populates="domain")
    users = relationship("UserRow", back_populates="domain")
    groups = relationship("GroupRow", back_populates="domain")
    scaling_groups = relationship(
        "ScalingGroupRow",
        secondary="sgroups_for_domains",
        back_populates="domains",
    )


class Domain(graphene.ObjectType):
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    total_resource_slots = graphene.JSONString()
    allowed_vfolder_hosts = graphene.JSONString()
    allowed_docker_registries = graphene.List(lambda: graphene.String)
    integration_id = graphene.String()

    # Dynamic fields.
    scaling_groups = graphene.List(lambda: graphene.String)

    async def resolve_scaling_groups(self, info: graphene.ResolveInfo) -> Sequence[str]:
        sgroups = await ScalingGroup.load_by_domain(info.context, self.name)
        return [sg.name for sg in sgroups]

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> Optional[Domain]:
        if row is None:
            return None
        return cls(
            name=row["name"],
            description=row["description"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
            total_resource_slots=(
                row["total_resource_slots"].to_json()
                if row["total_resource_slots"] is not None
                else {}
            ),
            allowed_vfolder_hosts=row["allowed_vfolder_hosts"].to_json(),
            allowed_docker_registries=row["allowed_docker_registries"],
            integration_id=row["integration_id"],
        )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        is_active: bool = None,
    ) -> Sequence[Domain]:
        async with ctx.db.begin_readonly() as conn:
            query = sa.select([domains]).select_from(domains)
            if is_active is not None:
                query = query.where(domains.c.is_active == is_active)
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def batch_load_by_name(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
        *,
        is_active: bool = None,
    ) -> Sequence[Optional[Domain]]:
        async with ctx.db.begin_readonly() as conn:
            query = sa.select([domains]).select_from(domains).where(domains.c.name.in_(names))
            if is_active is not None:
                query = query.where(domains.c.is_active == is_active)
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                names,
                lambda row: row["name"],
            )


class DomainInput(graphene.InputObjectType):
    description = graphene.String(required=False, default_value="")
    is_active = graphene.Boolean(required=False, default_value=True)
    total_resource_slots = graphene.JSONString(required=False, default_value={})
    allowed_vfolder_hosts = graphene.JSONString(required=False, default_value={})
    allowed_docker_registries = graphene.List(
        lambda: graphene.String, required=False, default_value=[]
    )
    integration_id = graphene.String(required=False, default_value=None)


class ModifyDomainInput(graphene.InputObjectType):
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    total_resource_slots = graphene.JSONString(required=False)
    allowed_vfolder_hosts = graphene.JSONString(required=False)
    allowed_docker_registries = graphene.List(lambda: graphene.String, required=False)
    integration_id = graphene.String(required=False)


class CreateDomain(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = DomainInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    domain = graphene.Field(lambda: Domain, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: DomainInput,
    ) -> CreateDomain:
        ctx: GraphQueryContext = info.context
        data = {
            "name": name,
            "description": props.description,
            "is_active": props.is_active,
            "total_resource_slots": ResourceSlot.from_user_input(props.total_resource_slots, None),
            "allowed_vfolder_hosts": props.allowed_vfolder_hosts,
            "allowed_docker_registries": props.allowed_docker_registries,
            "integration_id": props.integration_id,
        }
        insert_query = sa.insert(domains).values(data)

        async def _post_func(conn: SAConnection, result: Result) -> Row:
            from .group import groups

            model_store_insert_query = sa.insert(groups).values({
                "name": "model-store",
                "description": "Model Store",
                "is_active": True,
                "domain_name": name,
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "integration_id": None,
                "resource_policy": "default",
                "type": ProjectType.MODEL_STORE,
            })
            await conn.execute(model_store_insert_query)

        return await simple_db_mutate_returning_item(
            cls, ctx, insert_query, item_cls=Domain, post_func=_post_func
        )


class ModifyDomain(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyDomainInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    domain = graphene.Field(lambda: Domain, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: ModifyDomainInput,
    ) -> ModifyDomain:
        ctx: GraphQueryContext = info.context
        data: Dict[str, Any] = {}
        set_if_set(props, data, "name")  # data['name'] is new domain name
        set_if_set(props, data, "description")
        set_if_set(props, data, "is_active")
        set_if_set(
            props,
            data,
            "total_resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
        set_if_set(props, data, "allowed_vfolder_hosts")
        set_if_set(props, data, "allowed_docker_registries")
        set_if_set(props, data, "integration_id")
        update_query = sa.update(domains).values(data).where(domains.c.name == name)
        return await simple_db_mutate_returning_item(cls, ctx, update_query, item_cls=Domain)


class DeleteDomain(graphene.Mutation):
    """
    Instead of deleting the domain, just mark it as inactive.
    """

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(cls, root, info: graphene.ResolveInfo, name: str) -> DeleteDomain:
        ctx: GraphQueryContext = info.context
        update_query = sa.update(domains).values(is_active=False).where(domains.c.name == name)
        return await simple_db_mutate(cls, ctx, update_query)


class PurgeDomain(graphene.Mutation):
    """
    Completely delete domain from DB.

    Domain-bound kernels will also be all deleted.
    To purge domain, there should be no users and groups in the target domain.
    """

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(cls, root, info: graphene.ResolveInfo, name: str) -> PurgeDomain:
        from . import groups, users

        ctx: GraphQueryContext = info.context

        async def _pre_func(conn: SAConnection) -> None:
            if await cls.domain_has_active_kernels(conn, name):
                raise RuntimeError("Domain has some active kernels. Terminate them first.")
            query = sa.select([sa.func.count()]).where(users.c.domain_name == name)
            user_count = await conn.scalar(query)
            if user_count > 0:
                raise RuntimeError("There are users bound to the domain. Remove users first.")
            query = sa.select([sa.func.count()]).where(groups.c.domain_name == name)
            group_count = await conn.scalar(query)
            if group_count > 0:
                raise RuntimeError("There are groups bound to the domain. Remove groups first.")

            await cls.delete_kernels(conn, name)

        delete_query = sa.delete(domains).where(domains.c.name == name)
        return await simple_db_mutate(cls, ctx, delete_query, pre_func=_pre_func)

    @classmethod
    async def delete_kernels(
        cls,
        conn: SAConnection,
        domain_name: str,
    ) -> int:
        """
        Delete all kernels run from the target domain.

        :param conn: DB connection
        :param domain_name: domain's name to delete kernels

        :return: number of deleted rows
        """
        from . import kernels

        delete_query = sa.delete(kernels).where(kernels.c.domain_name == domain_name)
        result = await conn.execute(delete_query)
        if result.rowcount > 0:
            log.info('deleted {0} domain"s kernels ({1})', result.rowcount, domain_name)
        return result.rowcount

    @classmethod
    async def domain_has_active_kernels(
        cls,
        conn: SAConnection,
        domain_name: str,
    ) -> bool:
        """
        Check if the domain does not have active kernels.

        :param conn: DB connection
        :param domain_name: domain's name

        :return: True if the domain has some active kernels.
        """
        from . import AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES, kernels

        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(
                (kernels.c.domain_name == domain_name)
                & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
            )
        )
        active_kernel_count = await conn.scalar(query)
        return active_kernel_count > 0


class DomainDotfile(TypedDict):
    data: str
    path: str
    perm: str


async def query_domain_dotfiles(
    conn: SAConnection,
    name: str,
) -> tuple[List[DomainDotfile], int]:
    query = sa.select([domains.c.dotfiles]).select_from(domains).where(domains.c.name == name)
    packed_dotfile = await conn.scalar(query)
    if packed_dotfile is None:
        return [], MAXIMUM_DOTFILE_SIZE
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


def verify_dotfile_name(dotfile: str) -> bool:
    if dotfile in RESERVED_DOTFILES:
        return False
    return True
