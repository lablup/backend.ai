from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.session_template import SessionTemplateID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.manager.data.session_template.types import (
    SessionTemplateData,
    SessionTemplateWithOwnerEmailAndProjectName,
    TemplateType,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.models.domain.row import domains
from ai.backend.manager.models.keypair.row import keypairs
from ai.backend.manager.models.project.queriers import BulkProjectQuerier
from ai.backend.manager.models.session_template.creators import SessionTemplateCreator
from ai.backend.manager.models.session_template.row import SessionTemplateRow
from ai.backend.manager.models.session_template.scopes import SessionTemplateTarget
from ai.backend.manager.models.session_template.searchable_fields import (
    SessionTemplateSearchableFields,
)
from ai.backend.manager.models.session_template.searchers import SessionTemplateSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.user.queriers import BulkUserQuerier
from ai.backend.manager.models.user.queries import joined_project_ids_query
from ai.backend.manager.models.user.row import UserRole, users
from ai.backend.manager.models.virtual_entity.queries import user_scope_membership_exists
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.utils import check_if_requester_is_eligible_to_act_as_target_user

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TemplateDBSource:
    """Database source for session/cluster template operations."""

    _db: ExtendedAsyncSAEngine
    _ops: ShareOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, ops_provider: ShareOpsProvider) -> None:
        self._db = db
        self._ops = ops_provider

    # --- Owner resolution ---

    async def resolve_owner(
        self,
        requester_uuid: UserID,
        requester_access_key: str,
        requester_role: UserRole,
        requester_domain: str,
        requesting_domain: str,
        requesting_project_id: ProjectID,
        owner_access_key: str | None = None,
    ) -> tuple[UserID, ProjectID]:
        """Resolve owner UUID for template operations against a pre-resolved project.

        The caller is responsible for resolving the project name to ``requesting_project_id``
        (e.g. via ``ProjectRepository.project_id_by_name_in_domain``); this method handles
        on-behalf-of access-key delegation, domain validation, and role-based authorization.
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
                owner_uuid = UserID(row.user)
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

            # Authorize owner against the pre-resolved project
            if owner_role == UserRole.SUPERADMIN:
                pass  # already validated upstream by project-name resolution
            elif owner_role == UserRole.ADMIN:
                if requesting_domain != owner_domain:
                    raise InvalidAPIParameters("You can only set the domain to the owner's domain.")
            else:
                if requesting_domain != owner_domain:
                    raise InvalidAPIParameters("You can only set the domain to your domain.")
                membership_query = sa.select(
                    user_scope_membership_exists(
                        ProjectEntityType(), requesting_project_id, owner_uuid
                    )
                )
                if not await conn.scalar(membership_query):
                    raise InvalidAPIParameters("Invalid group")

        return owner_uuid, requesting_project_id

    # --- Task template operations ---

    async def create_task_templates(
        self,
        domain_name: str,
        items: list[dict[str, Any]],
    ) -> None:
        """Create one or more task templates. Each item must have: id, user_uuid, group_id, name, template."""
        creators = [
            SessionTemplateCreator(
                template_id=item["id"],
                template_type=TemplateType.TASK,
                domain_name=domain_name,
                user_uuid=item["user_uuid"],
                group_id=item["group_id"],
                name=item["name"],
                template=item["template"],
                created_at=datetime.now(UTC),
            )
            for item in items
        ]
        async with self._ops.write_ops() as w:
            await w.atomic_create_entities(creators)

    def _owning_scopes(
        self, user_uuid: UserID, group_id: ProjectID | None
    ) -> list[EntityIdentifier]:
        """The scopes a template with this owner and project is created in."""
        scopes: list[EntityIdentifier] = [user_uuid]
        if group_id is not None:
            scopes.append(group_id)
        return scopes

    async def get_task_template(self, template_id: SessionTemplateID) -> SessionTemplateData | None:
        """Get a single active task template by ID."""
        async with self._db.begin_readonly_session() as session:
            row = await session.scalar(self._active_template_query(template_id, TemplateType.TASK))
            if row is None:
                return None
            return SessionTemplateSearchableFields.own.to_data(row)

    async def task_template_exists(self, template_id: SessionTemplateID) -> bool:
        """Check if an active task template exists."""
        async with self._db.begin_readonly() as conn:
            q = (
                sa.select(SessionTemplateRow.id)
                .select_from(SessionTemplateRow)
                .where(
                    (SessionTemplateRow.id == template_id)
                    & (SessionTemplateRow.is_active)
                    & (SessionTemplateRow.type == TemplateType.TASK),
                )
            )
            result = await conn.scalar(q)
            return result is not None

    async def update_task_template(
        self,
        template_id: SessionTemplateID,
        group_id: ProjectID,
        user_uuid: UserID,
        name: str,
        template_data: Mapping[str, Any],
    ) -> int:
        """Update a task template; a changed owner or project moves it there. Returns rowcount."""
        async with self._db.begin() as conn:
            previous = (
                await conn.execute(
                    sa.select(SessionTemplateRow.user_uuid, SessionTemplateRow.group_id).where(
                        SessionTemplateRow.id == template_id
                    )
                )
            ).first()
            q = (
                sa.update(SessionTemplateRow)
                .values({
                    "group_id": group_id,
                    "user_uuid": user_uuid,
                    "name": name,
                    "template": template_data,
                })
                .where(SessionTemplateRow.id == template_id)
            )
            result = await conn.execute(q)
            rowcount = result.rowcount
        if previous is None:
            return rowcount
        from_scopes = self._owning_scopes(previous.user_uuid, previous.group_id)
        to_scopes = self._owning_scopes(user_uuid, group_id)
        if set(from_scopes) != set(to_scopes):
            async with self._ops.write_ops() as w:
                await w.transfer(from_scopes, to_scopes, template_id)
        return rowcount

    # --- Cluster template operations ---

    async def create_cluster_template(
        self,
        domain_name: str,
        group_id: ProjectID,
        user_uuid: UserID,
        name: str,
        template_data: Mapping[str, Any],
    ) -> SessionTemplateID:
        """Create a cluster template. Returns template ID."""
        template_id = SessionTemplateID(uuid4())
        async with self._ops.write_ops() as w:
            await w.create_entity(
                SessionTemplateCreator(
                    template_id=template_id,
                    template_type=TemplateType.CLUSTER,
                    domain_name=domain_name,
                    user_uuid=user_uuid,
                    group_id=group_id,
                    name=name,
                    template=template_data,
                    created_at=datetime.now(UTC),
                )
            )
        return template_id

    async def joined_project_ids(self, user_id: UserID) -> list[ProjectID]:
        """The projects the user is on the roster of, personal ones left out."""
        async with self._db.begin_readonly() as conn:
            joined_project_id_rows = await conn.scalars(joined_project_ids_query(user_id))
            return [ProjectID(project_id) for project_id in joined_project_id_rows.all()]

    async def list_templates_in_global(
        self, template_type: TemplateType
    ) -> list[SessionTemplateWithOwnerEmailAndProjectName]:
        """The active templates of ``template_type`` of every user and project."""
        async with self._ops.read_ops() as r:
            templates_found = await r.search_in_global(
                self._active_templates_searcher(template_type, None)
            )
            return await self._attach_owner_emails_and_project_names(r, templates_found.items)

    async def list_templates_in_scopes(
        self,
        template_type: TemplateType,
        scopes: Sequence[SessionTemplateTarget],
        group_id_filter: ProjectID | None,
    ) -> list[SessionTemplateWithOwnerEmailAndProjectName]:
        """The active templates of ``template_type`` that any of ``scopes`` holds."""
        async with self._ops.read_ops() as r:
            templates_found = await r.search_with_scopes(
                scopes, self._active_templates_searcher(template_type, group_id_filter)
            )
            return await self._attach_owner_emails_and_project_names(r, templates_found.items)

    def _active_templates_searcher(
        self, template_type: TemplateType, group_id_filter: ProjectID | None
    ) -> SessionTemplateSearcher:
        template_fields = SessionTemplateSearchableFields.own
        conditions = [
            template_fields.is_active.filter.equals(True),
            template_fields.type.filter.equals(template_type),
        ]
        if group_id_filter is not None:
            conditions.append(
                template_fields.group_id.filter.equals(
                    UUIDEqualMatchSpec(value=group_id_filter, negated=False)
                )
            )
        return SessionTemplateSearcher(pagination=NoPagination(), conditions=conditions)

    async def _attach_owner_emails_and_project_names(
        self, r: V2ReadOps, templates: Sequence[SessionTemplateData]
    ) -> list[SessionTemplateWithOwnerEmailAndProjectName]:
        owner_by_user_id = await r.query_bulk_data(
            BulkUserQuerier(), list({template.user_uuid for template in templates})
        )
        project_by_id = await r.query_bulk_data(
            BulkProjectQuerier(),
            list({template.group_id for template in templates if template.group_id is not None}),
        )
        entries: list[SessionTemplateWithOwnerEmailAndProjectName] = []
        for template in templates:
            owner = owner_by_user_id.get(template.user_uuid)
            project = (
                project_by_id.get(template.group_id) if template.group_id is not None else None
            )
            entries.append(
                SessionTemplateWithOwnerEmailAndProjectName(
                    template=template,
                    owner_email=owner.email if owner is not None else None,
                    project_name=project.name if project is not None else None,
                )
            )
        return entries

    async def get_cluster_template(
        self, template_id: SessionTemplateID
    ) -> SessionTemplateData | None:
        """Get a single active cluster template by ID."""
        async with self._db.begin_readonly_session() as session:
            row = await session.scalar(
                self._active_template_query(template_id, TemplateType.CLUSTER)
            )
            if row is None:
                return None
            return SessionTemplateSearchableFields.own.to_data(row)

    def _active_template_query(
        self, template_id: SessionTemplateID, template_type: TemplateType
    ) -> sa.Select[tuple[SessionTemplateRow]]:
        return sa.select(SessionTemplateRow).where(
            (SessionTemplateRow.id == template_id)
            & (SessionTemplateRow.is_active)
            & (SessionTemplateRow.type == template_type),
        )

    async def cluster_template_exists(self, template_id: SessionTemplateID) -> bool:
        """Check if an active cluster template exists."""
        async with self._db.begin_readonly() as conn:
            q = (
                sa.select(SessionTemplateRow.id)
                .select_from(SessionTemplateRow)
                .where(
                    (SessionTemplateRow.id == template_id)
                    & (SessionTemplateRow.is_active)
                    & (SessionTemplateRow.type == TemplateType.CLUSTER),
                )
            )
            result = await conn.scalar(q)
            return result is not None

    async def update_cluster_template(
        self,
        template_id: SessionTemplateID,
        template_data: Mapping[str, Any],
        name: str,
    ) -> int:
        """Update a cluster template. Returns rowcount."""
        async with self._db.begin() as conn:
            q = (
                sa.update(SessionTemplateRow)
                .values(template=template_data, name=name)
                .where(SessionTemplateRow.id == template_id)
            )
            result = await conn.execute(q)
            return result.rowcount

    # --- Shared operations ---

    async def soft_delete_template(
        self, template_id: SessionTemplateID, template_type: TemplateType
    ) -> int:
        """Soft-delete a template by setting is_active=False. Returns rowcount."""
        async with self._db.begin() as conn:
            q = (
                sa.update(SessionTemplateRow)
                .values(is_active=False)
                .where(
                    (SessionTemplateRow.id == template_id)
                    & (SessionTemplateRow.type == template_type),
                )
            )
            result = await conn.execute(q)
            return result.rowcount
