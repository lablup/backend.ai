from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa

from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.resource import DBOperationFailed
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import association_groups_users as agus
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.session_template import TemplateType, session_templates
from ai.backend.manager.models.user import UserRole, users
from ai.backend.manager.utils import check_if_requester_is_eligible_to_act_as_target_user

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TemplateDBSource:
    """Database source for session/cluster template operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # --- Owner resolution ---

    async def resolve_owner(
        self,
        requester_uuid: uuid.UUID,
        requester_access_key: str,
        requester_role: UserRole,
        requester_domain: str,
        requesting_domain: str,
        requesting_group: str,
        owner_access_key: str | None = None,
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """Resolve owner UUID and group ID for template operations.

        Adapted from utils.query_userinfo — handles on-behalf-of access key
        delegation, domain validation, and role-based group resolution.
        """
        async with self._db.begin_readonly() as conn:
            if owner_access_key is not None and owner_access_key != requester_access_key:
                query = (
                    sa.select(keypairs.c.user, users.c.role, users.c.domain_name)
                    .select_from(sa.join(keypairs, users, keypairs.c.user == users.c.uuid))
                    .where(keypairs.c.access_key == owner_access_key)
                )
                result = await conn.execute(query)
                row = result.first()
                if row is None:
                    raise InvalidAPIParameters("Unknown owner access key")
                owner_domain = row.domain_name
                owner_uuid = row.user
                owner_role = row.role
                try:
                    check_if_requester_is_eligible_to_act_as_target_user(
                        requester_role,
                        requester_domain,
                        owner_role,
                        owner_domain,
                    )
                except RuntimeError as e:
                    raise GenericForbidden(str(e)) from e
            else:
                owner_domain = requester_domain
                owner_uuid = requester_uuid
                owner_role = requester_role

            # Validate domain is active
            query = (
                sa.select(domains.c.name)
                .select_from(domains)
                .where((domains.c.name == owner_domain) & domains.c.is_active)
            )
            qresult = await conn.execute(query)
            if qresult.scalar() is None:
                raise InvalidAPIParameters("Invalid domain")

            # Resolve group by role
            if owner_role == UserRole.SUPERADMIN:
                query = (
                    sa.select(groups.c.id)
                    .select_from(groups)
                    .where(
                        (groups.c.domain_name == requesting_domain)
                        & (groups.c.name == requesting_group)
                        & groups.c.is_active,
                    )
                )
            elif owner_role == UserRole.ADMIN:
                if requesting_domain != owner_domain:
                    raise InvalidAPIParameters("You can only set the domain to the owner's domain.")
                query = (
                    sa.select(groups.c.id)
                    .select_from(groups)
                    .where(
                        (groups.c.domain_name == owner_domain)
                        & (groups.c.name == requesting_group)
                        & groups.c.is_active,
                    )
                )
            else:
                if requesting_domain != owner_domain:
                    raise InvalidAPIParameters("You can only set the domain to your domain.")
                query = (
                    sa.select(agus.c.group_id)
                    .select_from(agus.join(groups, agus.c.group_id == groups.c.id))
                    .where(
                        (agus.c.user_id == owner_uuid)
                        & (groups.c.domain_name == owner_domain)
                        & (groups.c.name == requesting_group)
                        & groups.c.is_active,
                    )
                )
            qresult = await conn.execute(query)
            group_id = qresult.scalar()
            if group_id is None:
                raise InvalidAPIParameters("Invalid group")

        return owner_uuid, group_id

    # --- Task template operations ---

    async def create_task_templates(
        self,
        domain_name: str,
        items: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        """Insert one or more task templates. Each item must have: id, user_uuid, group_id, name, template."""
        results: list[dict[str, str]] = []
        async with self._db.begin() as conn:
            for item in items:
                query = session_templates.insert().values({
                    "id": item["id"],
                    "created_at": datetime.now(UTC),
                    "domain_name": domain_name,
                    "group_id": item["group_id"],
                    "user_uuid": item["user_uuid"],
                    "name": item["name"],
                    "template": item["template"],
                    "type": TemplateType.TASK,
                })
                result = await conn.execute(query)
                if result.rowcount != 1:
                    raise DBOperationFailed(f"Failed to create session template: {item['id']}")
                results.append({"id": item["id"], "user": str(item["user_uuid"])})
        return results

    async def list_task_templates(self, user_uuid: uuid.UUID) -> list[dict[str, Any]]:
        """List all active task templates with user/group info."""
        async with self._db.begin_readonly() as conn:
            j = session_templates.join(
                users, session_templates.c.user_uuid == users.c.uuid, isouter=True
            ).join(groups, session_templates.c.group_id == groups.c.id, isouter=True)
            q = (
                sa.select(session_templates, users.c.email, groups.c.name)
                .set_label_style(sa.LABEL_STYLE_TABLENAME_PLUS_COL)
                .select_from(j)
                .where(
                    (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.TASK),
                )
            )
            result = await conn.execute(q)
            entries: list[dict[str, Any]] = []
            for row in result.fetchall():
                is_owner = row.session_templates_user_uuid == user_uuid
                entries.append({
                    "name": row.session_templates_name,
                    "id": row.session_templates_id,
                    "created_at": row.session_templates_created_at,
                    "is_owner": is_owner,
                    "user": (
                        str(row.session_templates_user_uuid)
                        if row.session_templates_user_uuid
                        else None
                    ),
                    "group": (
                        str(row.session_templates_group_id)
                        if row.session_templates_group_id
                        else None
                    ),
                    "user_email": row.users_email,
                    "group_name": row.groups_name,
                    "domain_name": None,
                    "type": row.session_templates_type,
                    "template": row.session_templates_template,
                })
            return entries

    async def get_task_template(self, template_id: str) -> dict[str, Any] | None:
        """Get a single active task template by ID."""
        async with self._db.begin_readonly() as conn:
            q = (
                sa.select(
                    session_templates.c.template,
                    session_templates.c.name,
                    session_templates.c.user_uuid,
                    session_templates.c.group_id,
                )
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.TASK),
                )
            )
            result = await conn.execute(q)
            row = result.first()
            if row is None:
                return None
            return {
                "template": row.template,
                "name": row.name,
                "user_uuid": row.user_uuid,
                "group_id": row.group_id,
            }

    async def task_template_exists(self, template_id: str) -> bool:
        """Check if an active task template exists."""
        async with self._db.begin_readonly() as conn:
            q = (
                sa.select(session_templates.c.id)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.TASK),
                )
            )
            result = await conn.scalar(q)
            return result is not None

    async def update_task_template(
        self,
        template_id: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        name: str,
        template_data: Mapping[str, Any],
    ) -> int:
        """Update a task template. Returns rowcount."""
        async with self._db.begin() as conn:
            q = (
                sa.update(session_templates)
                .values({
                    "group_id": group_id,
                    "user_uuid": user_uuid,
                    "name": name,
                    "template": template_data,
                })
                .where(session_templates.c.id == template_id)
            )
            result = await conn.execute(q)
            return result.rowcount

    # --- Cluster template operations ---

    async def create_cluster_template(
        self,
        domain_name: str,
        group_id: uuid.UUID,
        user_uuid: uuid.UUID,
        name: str,
        template_data: Mapping[str, Any],
    ) -> str:
        """Insert a cluster template. Returns template ID."""
        template_id = uuid.uuid4().hex
        async with self._db.begin() as conn:
            q = session_templates.insert().values({
                "id": template_id,
                "domain_name": domain_name,
                "group_id": group_id,
                "user_uuid": user_uuid,
                "name": name,
                "template": template_data,
                "type": TemplateType.CLUSTER,
            })
            result = await conn.execute(q)
            if result.rowcount != 1:
                raise DBOperationFailed(f"Failed to create cluster template: {template_id}")
        return template_id

    async def list_cluster_templates_all(self, user_uuid: uuid.UUID) -> list[dict[str, Any]]:
        """List all active cluster templates (superadmin + all mode)."""
        async with self._db.begin_readonly() as conn:
            j = session_templates.join(
                users, session_templates.c.user_uuid == users.c.uuid, isouter=True
            ).join(groups, session_templates.c.group_id == groups.c.id, isouter=True)
            q = (
                sa.select(session_templates, users.c.email, groups.c.name)
                .set_label_style(sa.LABEL_STYLE_TABLENAME_PLUS_COL)
                .select_from(j)
                .where(
                    (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.CLUSTER),
                )
            )
            result = await conn.execute(q)
            entries: list[dict[str, Any]] = []
            for row in result:
                is_owner = row.session_templates_user_uuid == user_uuid
                entries.append({
                    "name": row.session_templates_name,
                    "id": row.session_templates_id,
                    "created_at": row.session_templates_created_at,
                    "is_owner": is_owner,
                    "user": (
                        str(row.session_templates_user_uuid)
                        if row.session_templates_user_uuid
                        else None
                    ),
                    "group": (
                        str(row.session_templates_group_id)
                        if row.session_templates_group_id
                        else None
                    ),
                    "user_email": row.users_email,
                    "group_name": row.groups_name,
                })
            return entries

    async def list_accessible_cluster_templates(
        self,
        user_uuid: uuid.UUID,
        user_role: UserRole,
        domain_name: str,
        allowed_types: Iterable[str],
        group_id_filter: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        """List cluster templates accessible to a user based on role.

        Reimplements query_accessible_session_templates for TemplateType.CLUSTER.
        """
        extra_conds = None
        if group_id_filter is not None:
            extra_conds = session_templates.c.group_id == group_id_filter

        entries: list[dict[str, Any]] = []
        async with self._db.begin_readonly() as conn:
            if "user" in allowed_types:
                j = session_templates.join(users, session_templates.c.user_uuid == users.c.uuid)
                query = (
                    sa.select(
                        session_templates.c.name,
                        session_templates.c.id,
                        session_templates.c.created_at,
                        session_templates.c.user_uuid,
                        session_templates.c.group_id,
                        users.c.email,
                    )
                    .select_from(j)
                    .where(
                        (session_templates.c.user_uuid == user_uuid)
                        & session_templates.c.is_active
                        & (session_templates.c.type == TemplateType.CLUSTER),
                    )
                )
                if extra_conds is not None:
                    query = query.where(extra_conds)
                result = await conn.execute(query)
                for row in result:
                    entries.append({
                        "name": row.name,
                        "id": row.id,
                        "created_at": row.created_at,
                        "is_owner": True,
                        "user": str(row.user_uuid) if row.user_uuid else None,
                        "group": str(row.group_id) if row.group_id else None,
                        "user_email": row.email,
                        "group_name": None,
                    })

            if "group" in allowed_types:
                if user_role == UserRole.ADMIN:
                    grp_query = (
                        sa.select(groups.c.id)
                        .select_from(groups)
                        .where(groups.c.domain_name == domain_name)
                    )
                    result = await conn.execute(grp_query)
                    group_ids = [g.id for g in result.fetchall()]
                else:
                    j2 = sa.join(agus, users, agus.c.user_id == users.c.uuid)
                    grp_query = (
                        sa.select(agus.c.group_id)
                        .select_from(j2)
                        .where(agus.c.user_id == user_uuid)
                    )
                    result = await conn.execute(grp_query)
                    group_ids = [g.group_id for g in result.fetchall()]

                j3 = session_templates.join(groups, session_templates.c.group_id == groups.c.id)
                grp_tmpl_query = (
                    sa.select(
                        session_templates.c.name,
                        session_templates.c.id,
                        session_templates.c.created_at,
                        session_templates.c.user_uuid,
                        session_templates.c.group_id,
                        groups.c.name,
                    )
                    .set_label_style(sa.LABEL_STYLE_TABLENAME_PLUS_COL)
                    .select_from(j3)
                    .where(
                        session_templates.c.group_id.in_(group_ids)
                        & session_templates.c.is_active
                        & (session_templates.c.type == TemplateType.CLUSTER),
                    )
                )
                if extra_conds is not None:
                    grp_tmpl_query = grp_tmpl_query.where(extra_conds)
                if "user" in allowed_types:
                    grp_tmpl_query = grp_tmpl_query.where(
                        session_templates.c.user_uuid != user_uuid
                    )
                result = await conn.execute(grp_tmpl_query)
                is_owner = user_role == UserRole.ADMIN
                for row in result:
                    entries.append({
                        "name": row.session_templates_name,
                        "id": row.session_templates_id,
                        "created_at": row.session_templates_created_at,
                        "is_owner": is_owner,
                        "user": (
                            str(row.session_templates_user_uuid)
                            if row.session_templates_user_uuid
                            else None
                        ),
                        "group": (
                            str(row.session_templates_group_id)
                            if row.session_templates_group_id
                            else None
                        ),
                        "user_email": None,
                        "group_name": row.groups_name,
                    })
        return entries

    async def get_cluster_template(self, template_id: str) -> dict[str, Any] | None:
        """Get a single active cluster template by ID. Returns template dict or None."""
        async with self._db.begin_readonly() as conn:
            q = (
                sa.select(session_templates.c.template)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.CLUSTER),
                )
            )
            template = await conn.scalar(q)
            if template is None:
                return None
            if isinstance(template, dict):
                return template
            return dict(template)

    async def cluster_template_exists(self, template_id: str) -> bool:
        """Check if an active cluster template exists."""
        async with self._db.begin_readonly() as conn:
            q = (
                sa.select(session_templates.c.id)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.CLUSTER),
                )
            )
            result = await conn.scalar(q)
            return result is not None

    async def update_cluster_template(
        self,
        template_id: str,
        template_data: Mapping[str, Any],
        name: str,
    ) -> int:
        """Update a cluster template. Returns rowcount."""
        async with self._db.begin() as conn:
            q = (
                sa.update(session_templates)
                .values(template=template_data, name=name)
                .where(session_templates.c.id == template_id)
            )
            result = await conn.execute(q)
            return result.rowcount

    # --- Shared operations ---

    async def soft_delete_template(self, template_id: str, template_type: TemplateType) -> int:
        """Soft-delete a template by setting is_active=False. Returns rowcount."""
        async with self._db.begin() as conn:
            q = (
                sa.update(session_templates)
                .values(is_active=False)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.type == template_type),
                )
            )
            result = await conn.execute(q)
            return result.rowcount
