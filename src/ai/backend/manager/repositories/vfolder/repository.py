import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy import exc as sa_exc
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import (
    QuotaScopeID,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderID,
    VFolderMountPolicy,
)
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.entity_share.types import EntityShareData, EntityShareStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.project.types import ProjectResourceInfo
from ai.backend.manager.data.vfolder.dto import UserIdentity
from ai.backend.manager.data.vfolder.types import (
    UserWithVFolderHostPermissions,
    ValidatedVFolderInfo,
    VFolderCreation,
    VFolderData,
    VFolderInvitationData,
    VFolderMountPolicyData,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.errors.entity_share import EntityShareNotFound
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    RepositoryIntegrityError,
)
from ai.backend.manager.errors.resource import PersonalProjectNotFound, ProjectNotFound
from ai.backend.manager.errors.storage import (
    InsufficientStoragePermission,
    VFolderDeletionNotAllowed,
    VFolderFilterStatusFailed,
    VFolderHasLinkedModelCard,
    VFolderInvalidParameter,
    VFolderInvitationNotFound,
    VFolderNotFound,
    VFolderOperationFailed,
)
from ai.backend.manager.errors.user import KeyPairNotFound, UserNotFound
from ai.backend.manager.models.agent import agents
from ai.backend.manager.models.entity_share.creators import EntityShareCreator
from ai.backend.manager.models.entity_share.lookups import HeldShareLookup
from ai.backend.manager.models.entity_share.purgers import EntitySharePendingOfferBatchPurger
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.entity_share.updaters import (
    EntityShareAcceptUpdater,
    EntityShareCancelUpdater,
    EntityShareCapUpdater,
    EntityShareLeaveUpdater,
    EntityShareRejectUpdater,
    EntityShareRevokeUpdater,
)
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.keypair import KeyPairRow, keypairs
from ai.backend.manager.models.model_card.purgers import ModelCardPurger
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.project import ProjectRow, ProjectType
from ai.backend.manager.models.project.lookups import PersonalProjectOfUserLookup
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.types import ConflictCheck, IntegrityErrorCheck
from ai.backend.manager.models.user import (
    ACTIVE_USER_STATUSES,
    UserRole,
    UserRow,
    UserStatus,
    users,
)
from ai.backend.manager.models.user.lookups import UserEmailLookup
from ai.backend.manager.models.user.queries import joined_project_ids_query
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_retry
from ai.backend.manager.models.vfolder import (
    HARD_DELETED_VFOLDER_STATUSES,
    VFolderCloneInfo,
    VFolderDeletionInfo,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderRow,
    VFolderStatusSet,
    VFolderUserMountPolicyRow,
    ensure_host_permission_allowed,
    ensure_quota_scope_accessible_by_user,
    get_allowed_vfolder_hosts_by_group,
    get_allowed_vfolder_hosts_by_user,
    get_sessions_by_mounted_folder,
    is_unmanaged,
    vfolder_status_map,
    vfolders,
)
from ai.backend.manager.models.vfolder.creators import (
    PersonalVFolderCreator,
    ProjectVFolderCreator,
    VFolderBaseCreator,
)
from ai.backend.manager.models.vfolder.lookups import (
    VFolderNameLookup,
)
from ai.backend.manager.models.vfolder.purgers import (
    VFolderPurger,
    VFolderUserMountPolicyBatchPurger,
)
from ai.backend.manager.models.vfolder.queriers import (
    VFolderQuerier,
    VFolderUserMountPolicyQuerier,
)
from ai.backend.manager.models.vfolder.scopes import UserVFolderTarget
from ai.backend.manager.models.vfolder.searchable_fields import VFolderSearchableFields
from ai.backend.manager.models.vfolder.searchers import VFolderUserMountPolicySearcher
from ai.backend.manager.models.vfolder.updaters import (
    VFolderAttributeUpdater,
    VFolderReadyUpdater,
    VFolderSoftDeleteUpdater,
    VFolderTrashUpdater,
)
from ai.backend.manager.models.vfolder.upserters import VFolderUserMountPolicyUpserter
from ai.backend.manager.models.virtual_entity.queries import (
    user_scope_membership_exists,
)
from ai.backend.manager.repositories.base.integrity import match_integrity_error
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.ops.v2.share.write import V2ShareWriteOps
from ai.backend.manager.repositories.vfolder.purge_guards import (
    find_active_vfolder_references,
    vfolder_reference_conflict_checks,
)
from ai.backend.manager.repositories.vfolder.types import (
    BulkVFolderPurgeResult,
    VFolderPurgeFailure,
)

vfolder_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.VFOLDER_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


@dataclass
class _VFolderWithLinkedModelCards:
    """A vfolder row paired with model card rows referencing it."""

    vfolder_row: VFolderRow
    model_card_rows: list[ModelCardRow]


class VfolderRepository:
    _db: ExtendedAsyncSAEngine
    _v2_ops: ShareOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, v2_ops_provider: ShareOpsProvider) -> None:
        self._db = db
        self._v2_ops = v2_ops_provider

    @vfolder_repository_resilience.apply()
    async def get_by_id(self, vfolder_id: uuid.UUID) -> VFolderData:
        """
        Get a VFolder by ID without validation.
        Returns VFolderData if found, None otherwise.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
            if not vfolder_row:
                raise VFolderNotFound()
            return self._vfolder_row_to_data(vfolder_row)

    @vfolder_repository_resilience.apply()
    async def get_row_by_id(self, vfolder_id: VFolderUUID) -> Mapping[str, Any]:
        """
        Fetch a vfolder row as a plain mapping by UUID, without permission filtering.

        For use only by the REST middleware; do not call from new code.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
            if not vfolder_row:
                raise VFolderNotFound(extra_data=str(vfolder_id))
            return {
                "name": vfolder_row.name,
                "id": vfolder_row.id,
                "host": vfolder_row.host,
                "quota_scope_id": vfolder_row.quota_scope_id,
                "domain_name": vfolder_row.domain_name,
                "usage_mode": vfolder_row.usage_mode,
                "created_at": vfolder_row.created_at,
                "last_used": vfolder_row.last_used,
                "max_size": vfolder_row.max_size,
                "max_files": vfolder_row.max_files,
                "ownership_type": vfolder_row.ownership_type,
                "user": str(vfolder_row.user) if vfolder_row.user else None,
                "group": str(vfolder_row.group) if vfolder_row.group else None,
                "creator": vfolder_row.creator,
                "creator_id": vfolder_row.creator_id,
                "user_email": None,
                "group_name": None,
                "is_owner": False,
                "permission": vfolder_row.default_mount_permission,
                "unmanaged_path": vfolder_row.unmanaged_path,
                "cloneable": vfolder_row.cloneable,
                "status": vfolder_row.status,
                "cur_size": vfolder_row.cur_size,
            }

    @vfolder_repository_resilience.apply()
    async def batch_load_by_ids(self, ids: Sequence[uuid.UUID]) -> list[VFolderData | None]:
        """The named vfolders in the given order, ``None`` where an id matches no row.

        No permission check: the partial bulk action calling this has already
        narrowed ``ids`` to what the caller may read.
        """
        if not ids:
            return []
        async with self._db.begin_readonly_session() as session:
            id_in = VFolderSearchableFields.own.id.filter.in_(
                UUIDInMatchSpec(values=list(ids), negated=False)
            )
            query = sa.select(VFolderRow).where(id_in())
            result = await session.execute(query)
            rows_by_id = {row.id: self._vfolder_row_to_data(row) for row in result.scalars().all()}
            return [rows_by_id.get(VFolderUUID(vfolder_id)) for vfolder_id in ids]

    @vfolder_repository_resilience.apply()
    async def get_allowed_vfolder_hosts(
        self, user_uuid: uuid.UUID, group_uuid: uuid.UUID | None
    ) -> VFolderHostPermissionMap:
        """
        Get the allowed VFolder hosts for a user.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            if group_uuid:
                group_row: ProjectRow | None = await db_session.scalar(
                    sa.select(ProjectRow).where(ProjectRow.id == group_uuid)
                )
                if group_row is None:
                    raise ProjectNotFound(f"Project with {group_uuid} not found.")

                return group_row.allowed_vfolder_hosts

            allowed_hosts = await self._fetch_default_keypair_vfolder_hosts(db_session, user_uuid)
            if allowed_hosts is None:
                raise KeyPairNotFound("The user has no default keypair.")
            return allowed_hosts

    async def _fetch_default_keypair_vfolder_hosts(
        self, db_session: SASession, user_uuid: uuid.UUID
    ) -> VFolderHostPermissionMap | None:
        """
        Read ``allowed_vfolder_hosts`` from the resource policy of the user's default
        keypair. Returns ``None`` when the user has no default keypair.
        """
        stmt = (
            sa.select(
                KeyPairRow.access_key,
                keypair_resource_policies.c.allowed_vfolder_hosts,
            )
            .select_from(UserRow)
            .outerjoin(
                KeyPairRow,
                sa.and_(KeyPairRow.user == UserRow.uuid, KeyPairRow.is_default),
            )
            .outerjoin(
                keypair_resource_policies,
                keypair_resource_policies.c.name == KeyPairRow.resource_policy,
            )
            .where(UserRow.uuid == user_uuid)
        )
        row = (await db_session.execute(stmt)).first()
        if row is None:
            raise UserNotFound(f"User with UUID {user_uuid} not found.")
        # The host-permission column reads a SQL NULL back as an empty map, so the
        # keypair's own key is what tells an unmatched join apart from an empty policy.
        if row.access_key is None:
            return None
        allowed_hosts: VFolderHostPermissionMap = row.allowed_vfolder_hosts
        return allowed_hosts

    @vfolder_repository_resilience.apply()
    async def get_user_with_keypair_policy_vfolder_hosts(
        self, user_uuid: uuid.UUID
    ) -> UserWithVFolderHostPermissions:
        """
        Load user data together with the merged ``allowed_vfolder_hosts`` from
        all of the user's active keypair resource policies.

        A user can hold multiple keypairs, each pointing to its own keypair
        resource policy. This method unions ``allowed_vfolder_hosts`` across
        every active keypair so that the host-permission check reflects the
        full set of hosts available to the user (rather than only the default
        keypair).

        Implementation note: a single LEFT OUTER JOIN is used (instead of an
        ORM ``selectinload`` on ``UserRow.keypairs``) so that only the columns
        needed for the host-permission check are loaded. This avoids loading
        sensitive keypair columns such as ``secret_key`` and
        ``ssh_private_key``.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            stmt = (
                sa.select(
                    UserRow.email,
                    UserRow.role,
                    UserRow.domain_name,
                    keypair_resource_policies.c.allowed_vfolder_hosts,
                )
                .select_from(UserRow)
                .outerjoin(
                    KeyPairRow,
                    sa.and_(
                        KeyPairRow.user == UserRow.uuid,
                        KeyPairRow.is_active.is_(True),
                    ),
                )
                .outerjoin(
                    keypair_resource_policies,
                    keypair_resource_policies.c.name == KeyPairRow.resource_policy,
                )
                .where(UserRow.uuid == user_uuid)
            )
            rows = (await db_session.execute(stmt)).all()
            if not rows:
                raise UserNotFound(f"User with UUID {user_uuid} not found.")
            email, role, domain_name, _ = rows[0]
            if role is None or domain_name is None:
                raise UserNotFound(f"User with UUID {user_uuid} has invalid role or domain data.")
            merged_hosts = VFolderHostPermissionMap()
            for row in rows:
                policy_hosts = row.allowed_vfolder_hosts
                if policy_hosts is None:
                    continue
                merged_hosts = VFolderHostPermissionMap(merged_hosts | policy_hosts)
            return UserWithVFolderHostPermissions(
                email=email,
                role=role,
                allowed_vfolder_hosts=merged_hosts,
            )

    @vfolder_repository_resilience.apply()
    async def get_max_vfolder_count(
        self, user_uuid: uuid.UUID, group_uuid: uuid.UUID | None
    ) -> int:
        """
        Get the maximum VFolder count for a user or group.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            if group_uuid:
                group_row: ProjectRow | None = await db_session.scalar(
                    sa.select(ProjectRow)
                    .where(ProjectRow.id == group_uuid)
                    .options(selectinload(ProjectRow.resource_policy_row))
                )
                if group_row is None:
                    raise ProjectNotFound(f"Project with {group_uuid} not found.")

                return group_row.resource_policy_row.max_vfolder_count

            user_row: UserRow | None = await db_session.scalar(
                sa.select(UserRow)
                .where(UserRow.uuid == user_uuid)
                .options(selectinload(UserRow.resource_policy_row))
            )
            if user_row is None:
                raise UserNotFound(f"User with UUID {user_uuid} not found.")

            return user_row.resource_policy_row.max_vfolder_count

    @vfolder_repository_resilience.apply()
    async def resolve_vfolder_ids_by_names(self, names: Sequence[str]) -> dict[str, uuid.UUID]:
        """Look up vfolder UUIDs for a batch of names in a single query.

        Returns only the names that match an existing row; the caller
        decides what to do with any missing names (typically raise).

        No access scoping or status filtering — callers (e.g. session-create
        paths) are responsible for validating both user access and lifecycle
        state of the resolved ids in their own downstream flow.
        """
        if not names:
            return {}
        async with self._db.begin_readonly_session() as session:
            rows = (
                await session.execute(
                    sa.select(VFolderRow.name, VFolderRow.id).where(
                        VFolderRow.name.in_(list(names))
                    )
                )
            ).all()
        return {row.name: cast(uuid.UUID, row.id) for row in rows}

    @vfolder_repository_resilience.apply()
    async def get_personal_project_id(self, user_id: uuid.UUID) -> ProjectID:
        """The project what is given to a person lands in (BEP-1077 5.5).

        Answered by ``groups.creator_id`` on the personal project, which a partial
        unique index keeps to one per user. Raises ``PersonalProjectNotFound`` when the
        user has none: every user is given one, so the absence is a broken account and
        not a case to fall back from.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            project_id = await session.scalar(
                sa.select(ProjectRow.id).where(
                    ProjectRow.creator_id == user_id,
                    ProjectRow.type == ProjectType.PERSONAL,
                )
            )
            if project_id is None:
                raise PersonalProjectNotFound(f"User '{user_id}' has no personal project.")
            return ProjectID(project_id)

    @vfolder_repository_resilience.apply()
    async def create_vfolder_with_permission(self, creator: VFolderBaseCreator) -> VFolderCreation:
        """Write the vfolder row and answer with what making its storage folder needs.

        The host the folder asks for is checked here rather than by the caller, so a
        request that may not reach that host writes nothing.
        """
        await self.ensure_host_permission_allowed_by_user(
            creator.host,
            permission=VFolderHostPermission.CREATE,
            user_uuid=creator.creator_id,
            group_id=creator.project if isinstance(creator, ProjectVFolderCreator) else None,
        )
        max_quota_scope_size = await self._storage_limits(creator)
        async with self._v2_ops.write_ops() as w:
            created = await w.create_entity(creator)
            if isinstance(creator, ProjectVFolderCreator):
                # A project folder has no owner; its maker mounts it read-write through a
                # policy row the project may later change or take back.
                await w.upsert_field_entity(
                    created.id,
                    VFolderUserMountPolicyUpserter(
                        user_id=UserID(creator.creator_id),
                        permission=VFolderMountPolicy.READ_WRITE,
                    ),
                )
            return VFolderCreation(
                vfolder=created,
                max_quota_scope_size=max_quota_scope_size,
            )

    async def _storage_limits(self, creator: VFolderBaseCreator) -> int:
        """The quota scope size the folder is made with."""
        if isinstance(creator, ProjectVFolderCreator):
            project = await self.get_group_resource_info(creator.project, creator.domain_name)
            if project is None:
                raise ProjectNotFound(f"Project with {creator.project} not found.")
            return project.max_quota_scope_size
        user_info = await self.get_user_resource_info(creator.creator_id)
        if user_info is None:
            raise UserNotFound(f"User with {creator.creator_id} not found.")
        _, max_quota_scope_size, _ = user_info
        return max_quota_scope_size

    @vfolder_repository_resilience.apply()
    async def mark_vfolder_ready(self, vfolder_id: VFolderUUID) -> VFolderData:
        """Make a freshly created vfolder usable, its storage folder now there."""
        async with self._v2_ops.write_ops() as w:
            data = await w.update_data(VFolderReadyUpdater(vfolder_id=vfolder_id))
            if data is None:
                raise VFolderNotFound(extra_data=str(vfolder_id))
            return data

    @vfolder_repository_resilience.apply()
    async def trash_vfolder(self, updater: VFolderSoftDeleteUpdater) -> VFolderData:
        """Soft-delete a single vfolder by setting its status to DELETE_PENDING.

        Rejects the update while an active session mounts the vfolder; raises
        ``VFolderNotFound`` if no matching row exists.
        """
        # The mount key pairs the quota scope with the folder id, so it is read off the
        # row; the row's identity does not change, and the guard rides on the UPDATE.
        async with self._db.begin_readonly_session_read_committed() as session:
            vfolder_row = await self._get_vfolder_by_id(session, updater.vfolder_id)
            if vfolder_row is None:
                raise VFolderNotFound()
            mount_key = str(VFolderID.from_row(vfolder_row))

        async with self._v2_ops.write_ops() as w:
            data = await w.update_data(
                VFolderTrashUpdater(vfolder_id=updater.vfolder_id, mount_key=mount_key)
            )
            if data is None:
                raise VFolderNotFound()
            return data

    @vfolder_repository_resilience.apply()
    async def update_vfolder_attribute(self, updater: VFolderAttributeUpdater) -> VFolderData:
        """
        Update VFolder attributes.
        Returns updated VFolderData.
        """
        async with self._v2_ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise VFolderNotFound()
            return data

    @vfolder_repository_resilience.apply()
    async def move_vfolders_to_trash(self, vfolder_ids: list[uuid.UUID]) -> list[VFolderData]:
        """
        Move VFolders to trash.
        """

        async with self._db.begin_session() as session:
            vfolder_rows = []
            for vfolder_id in vfolder_ids:
                vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
                if vfolder_row:
                    vfolder_rows.append(vfolder_row)

            # Create deletion info for each vfolder
            deletion_infos = []
            for vfolder_row in vfolder_rows:
                vfolder_id_obj = VFolderID(
                    quota_scope_id=vfolder_row.quota_scope_id,
                    folder_id=vfolder_row.id,
                )
                deletion_info = VFolderDeletionInfo(
                    vfolder_id=vfolder_id_obj,
                    host=vfolder_row.host,
                    unmanaged_path=vfolder_row.unmanaged_path,
                )
                deletion_infos.append(deletion_info)

            # Note: initiate_vfolder_deletion requires storage_manager parameter
            # This would need to be passed to the repository method or handled differently
            # For now, we'll update the status directly instead of using the full deletion process
            for vfolder_row in vfolder_rows:
                if vfolder_row.status in VFolderOperationStatus.purge_in_progress():
                    raise VFolderFilterStatusFailed(f"VFolder is being purged: {vfolder_row.id}")
                mount_sessions = await get_sessions_by_mounted_folder(
                    session, VFolderID.from_row(vfolder_row)
                )
                if mount_sessions:
                    session_ids = [str(session_id) for session_id in mount_sessions]
                    raise VFolderDeletionNotAllowed(
                        "Cannot delete the vfolder. "
                        f"The vfolder(id: {vfolder_row.id}) is mounted on sessions(ids: {session_ids})."
                    )
                vfolder_row.status = VFolderOperationStatus.DELETE_PENDING

            await session.flush()
            for row in vfolder_rows:
                await session.refresh(row, attribute_names=["updated_at"])

            return [self._vfolder_row_to_data(row) for row in vfolder_rows]

    @vfolder_repository_resilience.apply()
    async def restore_vfolders_from_trash(self, vfolder_ids: list[uuid.UUID]) -> list[VFolderData]:
        """
        Restore VFolders from trash.
        """
        async with self._db.begin_session() as session:
            vfolder_rows = []
            for vfolder_id in vfolder_ids:
                vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
                if vfolder_row:
                    if vfolder_row.status in VFolderOperationStatus.purge_in_progress():
                        raise VFolderFilterStatusFailed(f"VFolder is being purged: {vfolder_id}")
                    vfolder_row.status = VFolderOperationStatus.READY
                    vfolder_rows.append(vfolder_row)

            await session.flush()
            for row in vfolder_rows:
                await session.refresh(row, attribute_names=["updated_at"])
            return [self._vfolder_row_to_data(row) for row in vfolder_rows]

    async def _fetch_vfolders_with_linked_model_cards(
        self,
        session: SASession,
        vfolder_ids: Sequence[uuid.UUID],
    ) -> list[_VFolderWithLinkedModelCards]:
        """Fetch vfolder rows together with model card rows that reference them.

        Uses a single LEFT OUTER JOIN. Vfolders with no model card appear
        once with an empty ``model_card_rows`` list; vfolder IDs not present
        in the database are skipped.
        """
        if not vfolder_ids:
            return []

        stmt = (
            sa.select(VFolderRow, ModelCardRow)
            .outerjoin(ModelCardRow, ModelCardRow.vfolder == VFolderRow.id)
            .where(VFolderRow.id.in_(vfolder_ids))
        )
        rows = (await session.execute(stmt)).all()

        grouped: dict[uuid.UUID, _VFolderWithLinkedModelCards] = {}
        for vfolder_row, card_row in rows:
            record = grouped.setdefault(
                vfolder_row.id,
                _VFolderWithLinkedModelCards(
                    vfolder_row=vfolder_row,
                    model_card_rows=[],
                ),
            )
            if card_row is not None:
                record.model_card_rows.append(card_row)
        return list(grouped.values())

    async def _ensure_vfolder_purgeable(
        self, session: SASession, vfolder_row: VFolderRow, *, force: bool
    ) -> None:
        """Raise when the vfolder must not be purged; return normally otherwise.

        Enforces a purgable-status precondition and rejects the purge while the
        vfolder is actively referenced anywhere in
        :data:`VFOLDER_REFERENCE_CHECKS` (live session/kernel mounts, active
        model-service endpoints via ``model`` or ``extra_mounts``). All checks
        are skipped when ``force`` is True.

        Raises:
            VFolderFilterStatusFailed: The vfolder status is not purgable.
            VFolderDeletionNotAllowed: The vfolder is still actively referenced.
        """
        if force:
            return
        if vfolder_row.status not in vfolder_status_map[VFolderStatusSet.PURGABLE]:
            raise VFolderFilterStatusFailed(
                f"Cannot purge the vfolder(id: {vfolder_row.id}). Its status "
                f"({vfolder_row.status.value}) is not purgable. Soft-delete it "
                "first or set force=True."
            )
        hits = await find_active_vfolder_references(session, vfolder_row)
        if hits:
            details = "; ".join(f"{hit.describe} {hit.referrer_ids}" for hit in hits)
            raise VFolderDeletionNotAllowed(
                f"Cannot purge the vfolder(id: {vfolder_row.id}); it is still in use: "
                f"{details}. Remove the reference(s) first or set force=True."
            )

    @vfolder_repository_resilience.apply()
    async def delete_vfolders_forever(
        self,
        vfolder_ids: list[uuid.UUID],
        *,
        cascade_model_card: bool = False,
        force: bool = False,
    ) -> BulkVFolderPurgeResult:
        """
        Delete VFolders forever with partial-success semantics.

        Each vfolder is processed independently in the same transaction:
        a vfolder with linked model card(s) becomes a failure (carrying
        ``VFolderHasLinkedModelCard``) when ``cascade_model_card`` is False;
        otherwise the cards are deleted and the vfolder transitions to
        ``DELETE_ONGOING`` like any other success.

        Unless ``force`` is True, a vfolder that is mounted by a live session,
        referenced by an active model-service endpoint, or not in a purgable
        status also becomes a failure (carrying the blocking error) and is
        skipped — its storage is left intact.
        """

        result = BulkVFolderPurgeResult()
        async with self._db.connect() as db_conn:
            async with self._db.begin_session(db_conn) as db_session:
                records = await self._fetch_vfolders_with_linked_model_cards(
                    db_session, vfolder_ids
                )
                card_ids_to_delete: list[ModelCardID] = []
                succeeded_ids: list[uuid.UUID] = []
                succeeded_rows: list[VFolderRow] = []
                for rec in records:
                    # Partial-success semantics: a per-vfolder blocker becomes a
                    # failure entry rather than aborting the whole batch.
                    try:
                        await self._ensure_vfolder_purgeable(
                            db_session, rec.vfolder_row, force=force
                        )
                    except BackendAIError as e:
                        result.failures.append(
                            VFolderPurgeFailure(vfolder_id=rec.vfolder_row.id, exception=e)
                        )
                        continue
                    if rec.model_card_rows and not cascade_model_card:
                        result.failures.append(
                            VFolderPurgeFailure(
                                vfolder_id=rec.vfolder_row.id,
                                exception=VFolderHasLinkedModelCard(
                                    f"VFolder {rec.vfolder_row.id} is referenced by "
                                    f"{len(rec.model_card_rows)} model card(s); "
                                    "delete the model card(s) first or set "
                                    "cascade_model_card=True."
                                ),
                            )
                        )
                        continue
                    card_ids_to_delete.extend(row.id for row in rec.model_card_rows)
                    succeeded_ids.append(rec.vfolder_row.id)
                    succeeded_rows.append(rec.vfolder_row)

                if card_ids_to_delete:
                    # A card is an entity of its own, so its graph goes with it. The
                    # purge runs in its own transaction; a failure after it leaves the
                    # folders alive and card-less, which a retry completes.
                    async with self._v2_ops.write_ops() as w:
                        for card_id in card_ids_to_delete:
                            await w.purge_entity(ModelCardPurger(card_id=card_id))

                if succeeded_ids:
                    delete_stmt = (
                        sa.update(VFolderRow)
                        .where(VFolderRow.id.in_(succeeded_ids))
                        .values(status=VFolderOperationStatus.DELETE_ONGOING)
                    )
                    await db_session.execute(delete_stmt)
                    # ``onupdate=now()`` on ``updated_at`` expires the
                    # column on the in-memory rows after the UPDATE;
                    # explicitly refresh so the subsequent conversion
                    # does not need a lazy SELECT (which would fail
                    # outside the greenlet bridge).
                    for row in succeeded_rows:
                        await db_session.refresh(row, attribute_names=["updated_at"])

                succeeded_data = [self._vfolder_row_to_data(row) for row in succeeded_rows]

            result.succeeded = succeeded_data
            return result

    @vfolder_repository_resilience.apply()
    async def purge_vfolder(self, vfolder_id: VFolderUUID, *, force: bool = False) -> VFolderData:
        """
        Permanently delete a VFolder from DB.
        Only VFolders with purgable status (DELETE_PENDING, DELETE_COMPLETE) can be purged.

        Unless ``force`` is True, the purge is rejected when the vfolder is
        mounted by a live session, referenced by an active model-service
        endpoint, or not in a purgable status. The in-use guard is carried by the
        purger spec as conflict checks, so the guard and the delete run in one
        transaction.

        Raises:
            VFolderNotFound: If the vfolder doesn't exist.
            VFolderFilterStatusFailed: If the vfolder status is not purgable.
            VFolderDeletionNotAllowed: If the vfolder is mounted or endpoint-referenced.
            VFolderHasLinkedModelCard: If a model card still references the vfolder.
        """
        async with self._v2_ops.write_ops() as w:
            vfolder = await w.query_data(VFolderQuerier(vfolder_id=vfolder_id))
            if vfolder is None:
                raise VFolderNotFound(extra_data=str(vfolder_id))
            reference_checks: Sequence[ConflictCheck] = ()
            if not force:
                if vfolder.status not in vfolder_status_map[VFolderStatusSet.PURGABLE]:
                    raise VFolderFilterStatusFailed(
                        f"Cannot purge the vfolder(id: {vfolder.id}). Its status "
                        f"({vfolder.status.value}) is not purgable. Soft-delete it "
                        "first or set force=True."
                    )
                reference_checks = vfolder_reference_conflict_checks(
                    VFolderID(vfolder.quota_scope_id, vfolder.id)
                )
            try:
                purged = await w.purge_entity(
                    VFolderPurger(vfolder_id=vfolder_id, reference_checks=reference_checks)
                )
            except RepositoryIntegrityError as e:
                match_integrity_error(
                    e,
                    [
                        IntegrityErrorCheck(
                            violation_type=ForeignKeyViolationError,
                            constraint_name="fk_model_cards_vfolder_vfolders",
                            error=VFolderHasLinkedModelCard(
                                f"VFolder {vfolder_id} cannot be purged: it is "
                                "still referenced by one or more model card(s). "
                                "Run delete-forever (with cascade if needed) "
                                "before purge."
                            ),
                        ),
                    ],
                )
            if purged is None:
                raise VFolderNotFound(extra_data=str(vfolder_id))
            return purged

    def _share_cap_of(self, permission: VFolderMountPolicy) -> Permission:
        """The access a legacy share request lends beside the mount level it names."""
        match permission:
            case VFolderMountPolicy.READ_WRITE:
                return Permission.READ | Permission.UPDATE | Permission.SOFT_DELETE
            case VFolderMountPolicy.READ_ONLY | VFolderMountPolicy.NONE:
                return Permission.READ

    async def _landing_project(self, w: V2ShareWriteOps, user_id: uuid.UUID) -> ProjectID:
        """Where what a person is given lands (BEP-1077 5.5).

        Read through the write ops so the scope, the policy row and the cap are settled
        in one transaction. Raises ``PersonalProjectNotFound`` when the user has none:
        every account is given one, so its absence is a broken account.
        """
        project_id = await w.lookup_entity_id(PersonalProjectOfUserLookup(user_id=UserID(user_id)))
        if project_id is None:
            raise PersonalProjectNotFound(f"User '{user_id}' has no personal project.")
        return project_id

    async def _lend_folder(
        self,
        w: V2ShareWriteOps,
        vfolder_id: VFolderUUID,
        user_id: uuid.UUID,
        permission: VFolderMountPolicy,
        sharer_id: UserID,
    ) -> VFolderMountPolicyData:
        """Give a user the folder at ``permission``: their mount level as a policy row
        and the access as a share, recorded and taken at once.

        A share already standing for the pair is restated instead of doubled.
        """
        recipient = UserID(user_id)
        policy = await w.upsert_field_entity(
            vfolder_id, VFolderUserMountPolicyUpserter(user_id=recipient, permission=permission)
        )
        creator = EntityShareCreator(
            sharer_user_id=sharer_id,
            target=vfolder_id,
            recipient=recipient,
            permission_cap=self._share_cap_of(permission),
        )
        if await w.restate_share(creator) is None:
            offered = await w.create_entity(creator)
            await w.accept_share(
                EntityShareAcceptUpdater(share_id=offered.id, answering_scope=recipient)
            )
        return policy

    async def _restate_lent_folder(
        self,
        w: V2ShareWriteOps,
        vfolder_id: VFolderUUID,
        user_id: uuid.UUID,
        permission: VFolderMountPolicy,
        sharer_id: UserID,
    ) -> VFolderMountPolicyData:
        """Set the mount level of a user the folder was already lent to, restating the
        share when one stands. The policy row is written either way."""
        recipient = UserID(user_id)
        policy = await w.upsert_field_entity(
            vfolder_id, VFolderUserMountPolicyUpserter(user_id=recipient, permission=permission)
        )
        await w.restate_share(
            EntityShareCreator(
                sharer_user_id=sharer_id,
                target=vfolder_id,
                recipient=recipient,
                permission_cap=self._share_cap_of(permission),
            )
        )
        return policy

    async def _take_back_folder(
        self, w: V2ShareWriteOps, vfolder_id: VFolderUUID, user_id: uuid.UUID
    ) -> None:
        """Take the folder back from a user: the share and its cap. The policy row
        stays and takes effect again when the user is given the folder anew."""
        held = await w.lookup_entity_id(
            HeldShareLookup(recipient=UserID(user_id), target=vfolder_id)
        )
        if held is not None:
            await w.revoke_share(EntityShareRevokeUpdater(share_id=held))
            return
        await w.unshare(await self._landing_project(w, user_id), [vfolder_id])

    @vfolder_repository_resilience.apply()
    async def revoke_shared_vfolder(self, vfolder_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Take a shared folder back from a user."""
        async with self._v2_ops.write_ops() as w:
            await self._take_back_folder(w, VFolderUUID(vfolder_id), user_id)

    @vfolder_repository_resilience.apply()
    async def leave_shared_vfolder(self, vfolder_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Give back a shared folder the user holds; silent when they hold nothing."""
        recipient = UserID(user_id)
        target = VFolderUUID(vfolder_id)
        async with self._v2_ops.write_ops() as w:
            held = await w.lookup_entity_id(HeldShareLookup(recipient=recipient, target=target))
            if held is not None:
                await w.revoke_share(
                    EntityShareLeaveUpdater(share_id=held, answering_scope=recipient)
                )
                return
            await w.unshare(await self._landing_project(w, user_id), [target])

    def _invitation_query(self) -> sa.Select[Any]:
        """Open vfolder offers with the folder offered, the sharer's email and name, and
        the mount level the invitee is set to get: their policy row, or the folder's
        default when none stands."""
        invitee = UserRow.__table__.alias("invitee")
        return (
            sa.select(
                EntityShareRow,
                VFolderRow,
                UserRow.email,
                UserRow.username,
                sa.func.coalesce(
                    VFolderUserMountPolicyRow.permission, VFolderRow.default_mount_permission
                ),
            )
            .select_from(EntityShareRow)
            .join(VFolderRow, VFolderRow.id == EntityShareRow.target_entity_id)
            .outerjoin(UserRow, UserRow.uuid == EntityShareRow.sharer_user_id)
            .outerjoin(
                invitee,
                sa.or_(
                    invitee.c.email == EntityShareRow.recipient_email,
                    invitee.c.uuid == EntityShareRow.recipient_entity_id,
                ),
            )
            .outerjoin(
                VFolderUserMountPolicyRow,
                sa.and_(
                    VFolderUserMountPolicyRow.vfolder_id == VFolderRow.id,
                    VFolderUserMountPolicyRow.user_id == invitee.c.uuid,
                ),
            )
            .where(
                EntityShareRow.target_entity_type == VFolderEntityType(),
                EntityShareRow.status == EntityShareStatus.PENDING,
            )
        )

    def _invitation_data(
        self,
        share_row: EntityShareRow,
        inviter_email: str | None,
        inviter_username: str | None,
        permission: VFolderMountPolicy,
    ) -> VFolderInvitationData:
        return VFolderInvitationData(
            id=share_row.id,
            vfolder=share_row.target_entity_id,
            inviter=inviter_email or "",
            inviter_username=inviter_username,
            invitee=share_row.recipient_email or "",
            permission=permission,
            created_at=share_row.created_at,
            modified_at=share_row.updated_at,
        )

    @vfolder_repository_resilience.apply()
    async def count_vfolders_by_user(self, user_id: uuid.UUID) -> int:
        """
        Count VFolders owned by a user (excluding hard deleted ones).
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(VFolderRow)
                .where(
                    (VFolderRow.user == user_id)
                    & (VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES))
                )
            )
            result = await session.scalar(query)
            return result or 0

    @vfolder_repository_resilience.apply()
    async def count_vfolders_by_group(self, group_id: uuid.UUID) -> int:
        """
        Count VFolders owned by a group (excluding hard deleted ones).
        """

        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(sa.func.count())
                .select_from(VFolderRow)
                .where(
                    (VFolderRow.group == group_id)
                    & (VFolderRow.ownership_type == VFolderOwnershipType.GROUP)
                    & (VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES))
                )
            )
            result = await session.scalar(query)
            return result or 0

    @vfolder_repository_resilience.apply()
    async def check_vfolder_name_exists(self, scope: OperationScope, name: str) -> bool:
        """Whether a vfolder the scope reaches, not hard-deleted, already carries the name."""
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(
                sa.select(VFolderRow.id)
                .where(
                    VFolderRow.name == name,
                    VFolderRow.status.not_in(HARD_DELETED_VFOLDER_STATUSES),
                    scope.to_condition()(),
                )
                .exists()
            )
            return bool(await session.scalar(query))

    @vfolder_repository_resilience.apply()
    async def resolve_vfolder_id_by_name(
        self, scopes: Sequence[OperationScope], name: str
    ) -> VFolderUUID:
        """The vfolder the name resolves to within the scopes."""
        async with self._v2_ops.read_ops() as r:
            vfolder_id = await r.lookup_entity_id(VFolderNameLookup(scopes=scopes, name=name))
        if vfolder_id is None:
            raise VFolderNotFound(extra_data=name)
        return vfolder_id

    @vfolder_repository_resilience.apply()
    async def get_joined_project_ids(self, user_id: UserID) -> list[ProjectID]:
        """The projects the user is on the roster of, personal ones left out."""
        async with self._db.begin_readonly_session_read_committed() as session:
            rows = await session.scalars(joined_project_ids_query(user_id))
            return [ProjectID(project_id) for project_id in rows.all()]

    @vfolder_repository_resilience.apply()
    async def get_user_info(self, user_id: uuid.UUID) -> tuple[UserRole, str] | None:
        """
        Get user role and domain name for a user.
        Returns (role, domain_name) or None if user not found.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            user_row = await session.scalar(sa.select(UserRow).where(UserRow.uuid == user_id))
            if not user_row:
                return None
            return user_row.role, user_row.domain_name

    @vfolder_repository_resilience.apply()
    async def get_user_email_by_id(self, user_id: uuid.UUID) -> str | None:
        """
        Get user email by user ID.
        Returns email or None if user not found.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            user_row = await session.scalar(sa.select(UserRow).where(UserRow.uuid == user_id))
            if not user_row:
                return None
            return user_row.email

    @vfolder_repository_resilience.apply()
    async def validate_quota_scope_access(
        self,
        quota_scope_id: QuotaScopeID,
        user_identity: UserIdentity,
    ) -> None:
        """
        Validate that the user has access to the given quota scope.
        Raises InvalidAPIParameters if the user does not have access.
        """
        user_info: Mapping[str, Any] = {
            "uuid": user_identity.user_uuid,
            "role": user_identity.user_role,
            "domain_name": user_identity.domain_name,
        }
        async with self._db.begin_readonly_session_read_committed() as session:
            await ensure_quota_scope_accessible_by_user(session, quota_scope_id, user_info)

    @vfolder_repository_resilience.apply()
    async def get_users_by_ids(self, user_ids: list[uuid.UUID]) -> list[tuple[uuid.UUID, str]]:
        """
        Get user info for multiple user IDs.
        Returns list of (user_id, email) tuples.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(sa.select(UserRow).where(UserRow.uuid.in_(user_ids)))
            user_rows = result.scalars().all()
            return [(row.uuid, row.email) for row in user_rows]

    @vfolder_repository_resilience.apply()
    async def get_group_resource_info(
        self, group_id_or_name: str | uuid.UUID, domain_name: str
    ) -> ProjectResourceInfo | None:
        """Get group resource information by group ID or name."""

        async with self._db.begin_readonly_session_read_committed() as session:
            if isinstance(group_id_or_name, str):
                query = (
                    sa.select(ProjectRow)
                    .where(
                        (ProjectRow.domain_name == domain_name)
                        & (ProjectRow.name == group_id_or_name)
                    )
                    .options(selectinload(ProjectRow.resource_policy_row))
                )
            else:  # UUID
                query = (
                    sa.select(ProjectRow)
                    .where(
                        (ProjectRow.domain_name == domain_name)
                        & (ProjectRow.id == group_id_or_name)
                    )
                    .options(selectinload(ProjectRow.resource_policy_row))
                )

            result = await session.execute(query)
            group_row = result.scalar()

            if not group_row:
                return None

            return ProjectResourceInfo(
                project_id=group_row.id,
                max_vfolder_count=group_row.resource_policy_row.max_vfolder_count,
                max_quota_scope_size=group_row.resource_policy_row.max_quota_scope_size,
                project_type=group_row.type,
            )

    @vfolder_repository_resilience.apply()
    async def get_user_resource_info(
        self, user_id: uuid.UUID
    ) -> tuple[int, int, int | None] | None:
        """
        Get user resource information.
        Returns (max_vfolder_count, max_quota_scope_size, container_uid) or None.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = (
                sa.select(UserRow)
                .where(UserRow.uuid == user_id)
                .options(selectinload(UserRow.resource_policy_row))
            )
            result = await session.execute(query)
            user_row = result.scalar()

            if not user_row:
                return None

            return (
                user_row.resource_policy_row.max_vfolder_count,
                user_row.resource_policy_row.max_quota_scope_size,
                user_row.container_uid,
            )

    async def _get_vfolder_by_id(
        self, session: SASession, vfolder_id: uuid.UUID
    ) -> VFolderRow | None:
        """
        Private method to get a VFolder by ID using an existing session.
        """
        query = sa.select(VFolderRow).where(VFolderRow.id == vfolder_id)
        result = await session.execute(query)
        return result.scalar()

    def _get_vfolder_scope(self, vfolder: VFolderData) -> ScopeId:
        """Determine scope from vfolder ownership."""
        if vfolder.ownership_type == VFolderOwnershipType.USER:
            return ScopeId(UserEntityType(), str(vfolder.user))
        # GROUP ownership
        return ScopeId(ProjectEntityType(), str(vfolder.group))

    async def _validate_vfolder_ownership(
        self, session: SASession, vfolder_id: uuid.UUID, user_id: uuid.UUID
    ) -> VFolderRow:
        """
        Private method to validate VFolder ownership.
        Raises VFolderNotFound if vfolder doesn't exist or user doesn't own it.
        """
        vfolder_row = await self._get_vfolder_by_id(session, vfolder_id)
        if not vfolder_row:
            raise VFolderNotFound()

        # Check ownership
        is_owner = False
        if vfolder_row.ownership_type == VFolderOwnershipType.USER:
            is_owner = vfolder_row.user == user_id
        elif vfolder_row.ownership_type == VFolderOwnershipType.GROUP:
            # TODO: check group membership
            pass

        if not is_owner:
            raise VFolderNotFound()

        return vfolder_row

    def _vfolder_row_to_data(self, row: VFolderRow) -> VFolderData:
        """
        Convert VFolderRow to VFolderData.
        """
        return VFolderData(
            id=row.id,
            name=row.name,
            host=row.host,
            domain_name=row.domain_name,
            quota_scope_id=row.quota_scope_id,
            usage_mode=row.usage_mode,
            default_mount_permission=row.default_mount_permission,
            created_at=row.created_at,
            last_used=row.last_used,
            updated_at=row.updated_at,
            creator=row.creator,
            creator_id=row.creator_id,
            unmanaged_path=row.unmanaged_path,
            ownership_type=row.ownership_type,
            user=row.user,
            group=row.group,
            cloneable=row.cloneable,
            status=row.status,
        )

    @vfolder_repository_resilience.apply()
    async def check_user_has_vfolder_permission(
        self, vfolder_id: uuid.UUID, user_ids: list[uuid.UUID]
    ) -> bool:
        """
        Check if any of the users already have permission for the vfolder.
        Returns True if any user already has permission.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            owns = sa.select(sa.literal(1)).where(
                VFolderRow.id == vfolder_id, VFolderRow.user.in_(user_ids)
            )
            holds = sa.select(sa.literal(1)).where(
                EntityShareRow.target_entity_type == VFolderEntityType(),
                EntityShareRow.target_entity_id == vfolder_id,
                EntityShareRow.status == EntityShareStatus.ACCEPTED,
                EntityShareRow.recipient_entity_type == UserEntityType(),
                EntityShareRow.recipient_entity_id.in_(user_ids),
            )
            found = await session.scalar(sa.select(sa.or_(owns.exists(), holds.exists())))
            return bool(found)

    @vfolder_repository_resilience.apply()
    async def get_user_by_email(self, email: str) -> tuple[uuid.UUID, str | None] | None:
        """
        Get user info by email.
        Returns (user_id, domain_name) or None if user not found.
        domain_name may be None.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            user_row = await session.scalar(sa.select(UserRow).where(UserRow.email == email))
            if not user_row:
                return None
            return user_row.uuid, user_row.domain_name

    @vfolder_repository_resilience.apply()
    async def get_users_by_emails(self, emails: list[str]) -> list[tuple[uuid.UUID, str]]:
        """
        Get user info for multiple emails.
        Returns list of (user_id, email) tuples.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(sa.select(UserRow).where(UserRow.email.in_(emails)))
            user_rows = result.scalars().all()
            return [(row.uuid, row.email) for row in user_rows]

    @vfolder_repository_resilience.apply()
    async def count_vfolder_with_name_for_user(self, user_id: uuid.UUID, vfolder_name: str) -> int:
        """
        Count VFolders with the given name accessible to the user.
        Used to check for duplicates when accepting invitations.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            lent = sa.select(sa.literal(1)).where(
                EntityShareRow.target_entity_type == VFolderEntityType(),
                EntityShareRow.target_entity_id == VFolderRow.id,
                EntityShareRow.status == EntityShareStatus.ACCEPTED,
                EntityShareRow.recipient_entity_type == UserEntityType(),
                EntityShareRow.recipient_entity_id == user_id,
            )
            query = (
                sa.select(sa.func.count())
                .select_from(VFolderRow)
                .where(
                    sa.or_(VFolderRow.user == user_id, lent.exists()),
                    VFolderRow.name == vfolder_name,
                    VFolderRow.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE]),
                )
            )
            result = await session.scalar(query)
            return result or 0

    @vfolder_repository_resilience.apply()
    async def create_vfolder_invitation(
        self,
        vfolder_id: uuid.UUID,
        inviter_id: UserID,
        invitee_email: str,
        permission: VFolderMountPolicy,
        *,
        invitee_id: UserID | None,
    ) -> str | None:
        """
        Offer the folder to the address, restating an offer already open to it, and
        set the mount level of the account the address belongs to. An address with no
        account gets the offer alone. Returns the invitee email when a new offer was
        written, None otherwise.
        """
        creator = EntityShareCreator(
            sharer_user_id=inviter_id,
            target=VFolderUUID(vfolder_id),
            recipient_email=invitee_email,
            permission_cap=self._share_cap_of(permission),
        )
        try:
            async with self._v2_ops.write_ops() as w:
                if invitee_id is not None:
                    await w.upsert_field_entity(
                        VFolderUUID(vfolder_id),
                        VFolderUserMountPolicyUpserter(user_id=invitee_id, permission=permission),
                    )
                if await w.restate_share(creator) is not None:
                    return None
                await w.create_entity(creator)
            return invitee_email
        except sa_exc.DataError:
            return None

    @vfolder_repository_resilience.apply()
    async def get_invitation_by_id(self, invitation_id: uuid.UUID) -> VFolderInvitationData | None:
        """
        Get a pending invitation by ID.
        Returns VFolderInvitationData or None if not found.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            query = self._invitation_query().where(EntityShareRow.id == invitation_id)
            row = (await session.execute(query)).one_or_none()
            if row is None:
                return None
            share_row, _, inviter_email, inviter_username, permission = row
            return self._invitation_data(
                share_row, inviter_email, inviter_username, VFolderMountPolicy(permission)
            )

    @vfolder_repository_resilience.apply()
    async def accept_invitation(self, invitation_id: uuid.UUID, invitee_id: UserID) -> None:
        """Settle the invitation as accepted and share the folder to the invitee.

        The mount level was set as a policy row when the offer was made.
        """
        async with self._v2_ops.write_ops() as w:
            try:
                accepted = await w.accept_share(
                    EntityShareAcceptUpdater(
                        share_id=EntityShareID(invitation_id), answering_scope=invitee_id
                    )
                )
            except EntityShareNotFound as e:
                raise VFolderInvitationNotFound() from e
            if accepted is None:
                raise VFolderInvitationNotFound()

    @vfolder_repository_resilience.apply()
    async def reject_invitation(self, invitation_id: uuid.UUID, invitee_id: UserID) -> None:
        """
        Turn down the invitation as its invitee.
        """
        async with self._v2_ops.write_ops() as w:
            try:
                rejected = await w.update_data(
                    EntityShareRejectUpdater(
                        share_id=EntityShareID(invitation_id), answering_scope=invitee_id
                    )
                )
            except EntityShareNotFound as e:
                raise VFolderInvitationNotFound() from e
            if rejected is None:
                raise VFolderInvitationNotFound()

    @vfolder_repository_resilience.apply()
    async def cancel_invitation(self, invitation_id: uuid.UUID) -> None:
        """
        Withdraw the invitation before it was answered.
        """
        async with self._v2_ops.write_ops() as w:
            try:
                canceled = await w.update_data(
                    EntityShareCancelUpdater(share_id=EntityShareID(invitation_id))
                )
            except EntityShareNotFound as e:
                raise VFolderInvitationNotFound() from e
            if canceled is None:
                raise VFolderInvitationNotFound()

    @vfolder_repository_resilience.apply()
    async def update_invitation_permission(
        self, invitation_id: uuid.UUID, inviter_id: UserID, permission: VFolderMountPolicy
    ) -> None:
        """
        Set what an open invitation lends and the mount level its invitee gets.
        Silent when the invitation is not the inviter's or was already answered.
        """
        async with self._v2_ops.write_ops() as w:
            try:
                updated = await w.update_data(
                    EntityShareCapUpdater(
                        share_id=EntityShareID(invitation_id),
                        sharer_user_id=inviter_id,
                        permission_cap=self._share_cap_of(permission),
                    )
                )
            except EntityShareNotFound:
                return
            if updated is None:
                return
            invitee = await self._invitee_of(w, updated)
            if invitee is None:
                return
            await w.upsert_field_entity(
                VFolderUUID(updated.target),
                VFolderUserMountPolicyUpserter(user_id=invitee, permission=permission),
            )

    async def _invitee_of(self, w: V2ShareWriteOps, share: EntityShareData) -> UserID | None:
        """The account an offer is addressed to; ``None`` while the address has none."""
        if share.recipient is not None and share.recipient.entity_type() == UserEntityType():
            return UserID(share.recipient)
        if share.recipient_email is None:
            return None
        return await w.lookup_entity_id(UserEmailLookup(email=share.recipient_email))

    @vfolder_repository_resilience.apply()
    async def update_invited_vfolder_mount_permission(
        self,
        vfolder_id: uuid.UUID,
        user_id: uuid.UUID,
        permission: VFolderMountPolicy,
        *,
        sharer_id: UserID,
    ) -> None:
        """
        Set the mount level of a user the folder was lent to.
        """
        async with self._v2_ops.write_ops() as w:
            await self._restate_lent_folder(
                w, VFolderUUID(vfolder_id), user_id, permission, sharer_id
            )

    @vfolder_repository_resilience.apply()
    async def get_pending_invitations_for_user(
        self, user_id: UserID, user_email: str
    ) -> list[tuple[VFolderInvitationData, VFolderData]]:
        """
        Get all pending invitations for a user with VFolder info.
        Returns list of (invitation_data, vfolder_data) tuples.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            addressed = sa.or_(
                EntityShareRow.recipient_email == user_email,
                sa.and_(
                    EntityShareRow.recipient_entity_type == UserEntityType(),
                    EntityShareRow.recipient_entity_id == user_id,
                ),
            )
            result = await session.execute(self._invitation_query().where(addressed))
            return [
                (
                    self._invitation_data(
                        share_row, inviter_email, inviter_username, VFolderMountPolicy(permission)
                    ),
                    self._vfolder_row_to_data(vfolder_row),
                )
                for share_row, vfolder_row, inviter_email, inviter_username, permission in result
            ]

    @vfolder_repository_resilience.apply()
    async def get_sent_invitations_for_user(
        self, user_id: UserID
    ) -> list[tuple[VFolderInvitationData, VFolderData]]:
        """
        Get all pending invitations sent by a user (as inviter) with VFolder info.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            result = await session.execute(
                self._invitation_query().where(EntityShareRow.sharer_user_id == user_id)
            )
            return [
                (
                    self._invitation_data(
                        share_row, inviter_email, inviter_username, VFolderMountPolicy(permission)
                    ),
                    self._vfolder_row_to_data(vfolder_row),
                )
                for share_row, vfolder_row, inviter_email, inviter_username, permission in result
            ]

    @vfolder_repository_resilience.apply()
    async def ensure_host_permission_allowed(
        self,
        folder_host: str,
        *,
        permission: VFolderHostPermission,
        allowed_vfolder_types: Sequence[str],
        user_uuid: uuid.UUID,
        resource_policy: Mapping[str, Any],
        domain_name: str,
        group_id: uuid.UUID | None = None,
    ) -> None:
        """
        Ensure that the user has the required permission on the specified vfolder host.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            # Get connection from session
            conn = await session.connection()
            await ensure_host_permission_allowed(
                conn,
                folder_host,
                permission=permission,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=user_uuid,
                resource_policy=resource_policy,
                domain_name=domain_name,
                group_id=group_id,
            )

    @vfolder_repository_resilience.apply()
    async def ensure_host_permission_allowed_by_user(
        self,
        folder_host: str,
        *,
        permission: VFolderHostPermission,
        user_uuid: uuid.UUID,
        group_id: uuid.UUID | None = None,
    ) -> None:
        """Check host permission by looking up the user's resource policy from DB."""
        allowed_hosts = await self.get_allowed_vfolder_hosts(user_uuid, group_id)
        if folder_host not in allowed_hosts or permission not in allowed_hosts[folder_host]:
            raise InsufficientStoragePermission(
                f"`{permission}` Not allowed in vfolder host(`{folder_host}`)"
            )

    @vfolder_repository_resilience.apply()
    async def get_validated_vfolder_id(
        self,
        vfolder_uuid: uuid.UUID,
        *,
        permission: VFolderHostPermission,
        allowed_vfolder_types: Sequence[str],
        resource_policy: Mapping[str, Any],
    ) -> ValidatedVFolderInfo:
        """
        Resolve user from context, validate vfolder access, check host permission,
        and return validated VFolderID with storage info.
        """
        user = current_user()
        if user is None:
            raise AuthorizationFailed("User context is not available")
        vfolder_data = await self.get_by_id(vfolder_uuid)
        await self.ensure_host_permission_allowed(
            vfolder_data.host,
            permission=permission,
            allowed_vfolder_types=allowed_vfolder_types,
            user_uuid=user.user_id,
            resource_policy=resource_policy,
            domain_name=vfolder_data.domain_name,
        )
        return ValidatedVFolderInfo(
            vfolder_id=VFolderID(
                quota_scope_id=vfolder_data.quota_scope_id,
                folder_id=vfolder_data.id,
            ),
            host=vfolder_data.host,
            unmanaged_path=vfolder_data.unmanaged_path,
        )

    @vfolder_repository_resilience.apply()
    async def initiate_vfolder_clone(
        self,
        vfolder_info: VFolderCloneInfo,
        storage_manager: StorageSessionManager,
        _background_task_manager: BackgroundTaskManager,
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """
        Initiate VFolder cloning process.
        Returns (task_id, target_folder_id).
        """
        source_vf_cond = vfolders.c.id == vfolder_info.source_vfolder_id.folder_id

        async def _update_source_status() -> None:
            async with self._db.begin_session() as db_session:
                query = (
                    sa.update(vfolders)
                    .values(status=VFolderOperationStatus.CLONING)
                    .where(source_vf_cond)
                )
                await db_session.execute(query)

        await execute_with_retry(_update_source_status)

        target_proxy, target_volume = storage_manager.get_proxy_and_volume(vfolder_info.target_host)
        source_proxy, source_volume = storage_manager.get_proxy_and_volume(
            vfolder_info.source_host, is_unmanaged(vfolder_info.unmanaged_path)
        )

        if source_proxy != target_proxy:
            raise VFolderInvalidParameter(
                f"Proxy names of source and target vfolders must be equal. "
                f"Source proxy: {source_proxy}, Target proxy: {target_proxy}."
            )

        # The destination row lands first so the database names it, and it stays
        # unusable until the storage proxy has copied the contents into it. A clone
        # target is always user-owned, and it goes through the entity creator so the
        # RBAC scope association lands with the row.
        async with self._v2_ops.write_ops() as w:
            target = await w.create_entity(
                PersonalVFolderCreator(
                    name=vfolder_info.target_vfolder_name,
                    domain_name=vfolder_info.domain_name,
                    quota_scope_id=str(vfolder_info.target_quota_scope_id),
                    host=vfolder_info.target_host,
                    creator_id=vfolder_info.user_id,
                    usage_mode=vfolder_info.usage_mode,
                    default_mount_permission=vfolder_info.permission,
                    user=UserID(vfolder_info.user_id),
                    cloneable=vfolder_info.cloneable,
                    status=VFolderOperationStatus.CREATING,
                )
            )
        target_folder_id = VFolderID(vfolder_info.target_quota_scope_id, target.id)

        # Clone the vfolder contents
        manager_client = storage_manager.get_manager_facing_client(source_proxy)
        try:
            clone_response = await manager_client.clone_folder(
                source_volume,
                str(vfolder_info.source_vfolder_id),
                target_volume,
                str(target_folder_id),
            )
        except Exception:
            await self.purge_vfolder(target.id)
            raise
        await self.mark_vfolder_ready(target.id)

        return clone_response.bgtask_id, target.id

    @vfolder_repository_resilience.apply()
    async def get_logs_vfolder(self, user_id: UserID) -> VFolderData | None:
        """The ``.logs`` vfolder the user reaches, or ``None`` when there is none."""
        async with self._v2_ops.read_ops() as r:
            vfolder_id = await r.lookup_entity_id(
                VFolderNameLookup(scopes=[UserVFolderTarget(user_id=user_id)], name=".logs")
            )
        if vfolder_id is None:
            return None
        return await self.get_by_id(vfolder_id)

    @vfolder_repository_resilience.apply()
    async def share_vfolder_with_users(
        self,
        vfolder_id: uuid.UUID,
        vfolder_host: str,
        vfolder_group: uuid.UUID | None,
        requester_uuid: uuid.UUID,
        requester_email: str,
        domain_name: str,
        resource_policy: Mapping[str, Any],
        emails: list[str],
        permission: VFolderMountPolicy,
        allowed_vfolder_types: Sequence[str],
    ) -> list[str]:
        """
        Share a group vfolder with users by granting permissions directly.
        Returns list of emails that were shared with.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            conn = await session.connection()
            await ensure_host_permission_allowed(
                conn,
                vfolder_host,
                permission=VFolderHostPermission.SET_USER_PERM,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=requester_uuid,
                resource_policy=resource_policy,
                domain_name=domain_name,
            )

            if vfolder_group is None:
                # Sharing targets a group vfolder; a folder without an owning
                # project cannot be shared with project members.
                raise VFolderInvalidParameter("Only group vfolders can be shared with users.")
            users_table = UserRow.__table__
            db_query = sa.select(users_table.c.uuid, users_table.c.email).where(
                user_scope_membership_exists(
                    ProjectEntityType(), vfolder_group, users_table.c.uuid
                ),
                users_table.c.email.in_(emails),
                users_table.c.email != requester_email,
                users_table.c.status.in_(ACTIVE_USER_STATUSES),
            )
            result = await session.execute(db_query)
            user_info = result.fetchall()
            users_to_share = [u.uuid for u in user_info]
            emails_to_share = [u.email for u in user_info]
            if len(user_info) < 1:
                raise UserNotFound()
            if len(user_info) < len(emails):
                users_not_in_group = list(set(emails) - set(emails_to_share))
                raise UserNotFound(
                    f"Some users do not belong to folder's group: {','.join(users_not_in_group)}"
                )

        async with self._v2_ops.write_ops() as w:
            for user_id in users_to_share:
                await self._lend_folder(
                    w, VFolderUUID(vfolder_id), user_id, permission, UserID(requester_uuid)
                )
        return emails_to_share

    @vfolder_repository_resilience.apply()
    async def unshare_vfolder_from_users(
        self,
        vfolder_id: uuid.UUID,
        vfolder_host: str,
        requester_uuid: uuid.UUID,
        domain_name: str,
        resource_policy: Mapping[str, Any],
        emails: list[str],
        allowed_vfolder_types: Sequence[str],
    ) -> list[str]:
        """
        Revoke direct sharing permissions from users.
        Returns list of emails that were unshared.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            conn = await session.connection()
            await ensure_host_permission_allowed(
                conn,
                vfolder_host,
                permission=VFolderHostPermission.SET_USER_PERM,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=requester_uuid,
                resource_policy=resource_policy,
                domain_name=domain_name,
            )

            users_table = UserRow.__table__
            db_query = (
                sa.select(users_table.c.uuid)
                .select_from(users_table)
                .where(users_table.c.email.in_(emails))
            )
            result = await session.execute(db_query)
            users_to_unshare = [u.uuid for u in result.fetchall()]
            if len(users_to_unshare) < 1:
                raise UserNotFound()

        async with self._v2_ops.write_ops() as w:
            for user_id in users_to_unshare:
                await self._take_back_folder(w, VFolderUUID(vfolder_id), user_id)
        return emails

    @vfolder_repository_resilience.apply()
    async def set_user_mount_policy(
        self, vfolder_id: VFolderUUID, user_id: UserID, permission: VFolderMountPolicy
    ) -> VFolderMountPolicyData:
        """Set the mount level one user gets on the folder, replacing what stood."""
        async with self._v2_ops.write_ops() as w:
            return await w.upsert_field_entity(
                vfolder_id,
                VFolderUserMountPolicyUpserter(user_id=user_id, permission=permission),
            )

    @vfolder_repository_resilience.apply()
    async def unset_user_mount_policy(self, vfolder_id: VFolderUUID, user_id: UserID) -> bool:
        """Take back the mount level one user was given; False when they had none."""
        async with self._v2_ops.write_ops() as w:
            purged = await w.batch_purge_field_entities(
                vfolder_id, VFolderUserMountPolicyBatchPurger(user_id=user_id)
            )
            return bool(purged)

    @vfolder_repository_resilience.apply()
    async def list_user_mount_policies(
        self, vfolder_id: VFolderUUID
    ) -> list[VFolderMountPolicyData]:
        """The mount levels set on the folder, one row per user."""
        async with self._v2_ops.read_ops() as r:
            result = await r.search_in_global(
                VFolderUserMountPolicySearcher(pagination=NoPagination(), vfolder_id=vfolder_id)
            )
            return result.items

    @vfolder_repository_resilience.apply()
    async def user_mount_policies_of(
        self, user_id: UserID, vfolder_ids: Sequence[VFolderUUID]
    ) -> Mapping[VFolderUUID, VFolderMountPolicy]:
        """The mount level rows one user holds, keyed by folder; a folder without one
        is absent."""
        async with self._v2_ops.read_ops() as r:
            rows = await r.query_owned_fields(
                VFolderUserMountPolicyQuerier(user_id=user_id), vfolder_ids
            )
            return {vfolder_id: data.permission for vfolder_id, data in rows.items()}

    @vfolder_repository_resilience.apply()
    async def list_shared_vfolder_permissions(
        self,
        requester_id: UserID | None = None,
        vfolder_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        """
        List the users each vfolder is lent to, with the mount level each gets: their
        policy row, or the folder's default when none stands.

        ``requester_id`` keeps the entries the user is party to: the share is granted
        to them, or it stands on a folder they own, created, or reach through their
        project membership. Omitting it lists every entry in the system.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            share_table = EntityShareRow.__table__
            vf_table = VFolderRow.__table__
            users_table = UserRow.__table__
            policy_table = VFolderUserMountPolicyRow.__table__
            j = (
                share_table.join(vf_table, vf_table.c.id == share_table.c.target_entity_id)
                .join(users_table, users_table.c.uuid == share_table.c.recipient_entity_id)
                .outerjoin(
                    policy_table,
                    sa.and_(
                        policy_table.c.vfolder_id == vf_table.c.id,
                        policy_table.c.user_id == share_table.c.recipient_entity_id,
                    ),
                )
            )
            db_query = (
                sa.select(
                    share_table.c.recipient_entity_id.label("user"),
                    sa.func.coalesce(
                        policy_table.c.permission, vf_table.c.default_mount_permission
                    ).label("permission"),
                    vf_table.c.id.label("vfolder_id"),
                    vf_table.c.name,
                    vf_table.c.group,
                    vf_table.c.ownership_type,
                    vf_table.c.status,
                    vf_table.c.user.label("vfolder_user"),
                    users_table.c.email,
                )
                .select_from(j)
                .where(
                    share_table.c.target_entity_type == VFolderEntityType(),
                    share_table.c.recipient_entity_type == UserEntityType(),
                    share_table.c.status == EntityShareStatus.ACCEPTED,
                )
            )
            if vfolder_id is not None:
                db_query = db_query.where(vf_table.c.id == vfolder_id)
            if requester_id is not None:
                db_query = db_query.where(
                    sa.or_(
                        share_table.c.recipient_entity_id == requester_id,
                        vf_table.c.user == requester_id,
                        vf_table.c.creator_id == requester_id,
                        user_scope_membership_exists(
                            ProjectEntityType(), vf_table.c.group, requester_id
                        ),
                    )
                )
            result = await session.execute(db_query)
            return [dict(row._mapping) for row in result.fetchall()]

    @vfolder_repository_resilience.apply()
    async def update_vfolder_sharing_status(
        self,
        vfolder_id: uuid.UUID,
        to_delete: list[uuid.UUID],
        to_update: list[tuple[uuid.UUID, VFolderMountPolicy]],
        *,
        sharer_id: UserID,
    ) -> None:
        """
        Batch update and/or delete sharing permissions for a vfolder.
        """
        async with self._v2_ops.write_ops() as w:
            for user_id in to_delete:
                await self._take_back_folder(w, VFolderUUID(vfolder_id), user_id)
            for user_id, perm in to_update:
                await self._restate_lent_folder(
                    w, VFolderUUID(vfolder_id), user_id, perm, sharer_id
                )

    @vfolder_repository_resilience.apply()
    async def update_vfolder_max_size(
        self,
        vfolder_id: uuid.UUID,
        max_size_mib: int,
    ) -> None:
        """
        Update the max_size field of a vfolder in MiB.
        """
        async with self._db.begin_session() as session:
            conn = await session.connection()
            update_query = (
                sa.update(vfolders).values(max_size=max_size_mib).where(vfolders.c.id == vfolder_id)
            )
            db_result = await conn.execute(update_query)
            if db_result.rowcount != 1:
                raise VFolderOperationFailed(
                    f"Failed to update vfolder quota: expected 1 row, got {db_result.rowcount}"
                )

    @vfolder_repository_resilience.apply()
    async def get_user_storage_host_permissions(
        self,
        user_uuid: uuid.UUID,
        domain_name: str,
    ) -> VFolderHostPermissionMap:
        """
        Resolve all storage hosts and per-host permissions accessible to a user.

        Internally fetches the user's default keypair resource policy and unions
        domain/group/keypair allowed vfolder hosts. Returns the host permission
        map without filtering against currently mountable volumes — callers that
        depend on volume availability must intersect with ``StorageSessionManager``.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            allowed_hosts = await self._fetch_default_keypair_vfolder_hosts(db_session, user_uuid)
            resource_policy: Mapping[str, Any] = {
                "allowed_vfolder_hosts": allowed_hosts
                if allowed_hosts is not None
                else VFolderHostPermissionMap(),
            }
            conn = await db_session.connection()
            return await get_allowed_vfolder_hosts_by_user(
                conn=conn,
                resource_policy=resource_policy,
                domain_name=domain_name,
                user_uuid=user_uuid,
                group_id=None,
            )

    @vfolder_repository_resilience.apply()
    async def get_allowed_hosts_for_listing(
        self,
        user_uuid: uuid.UUID,
        domain_name: str,
        group_id: uuid.UUID | None,
        resource_policy: Mapping[str, Any],
        allowed_vfolder_types: Sequence[str],
    ) -> VFolderHostPermissionMap:
        """
        Get the combined allowed vfolder hosts for user and group.
        """
        async with self._db.begin_readonly_session() as session:
            conn = await session.connection()
            allowed_hosts = VFolderHostPermissionMap()
            if "user" in allowed_vfolder_types:
                allowed_hosts_by_user = await get_allowed_vfolder_hosts_by_user(
                    conn, resource_policy, domain_name, user_uuid, group_id
                )
                allowed_hosts = cast(
                    VFolderHostPermissionMap, allowed_hosts | allowed_hosts_by_user
                )
            if "group" in allowed_vfolder_types:
                allowed_hosts_by_group = await get_allowed_vfolder_hosts_by_group(
                    conn,
                    resource_policy,
                    domain_name,
                    group_id,
                )
                allowed_hosts = cast(
                    VFolderHostPermissionMap, allowed_hosts | allowed_hosts_by_group
                )
            return allowed_hosts

    @vfolder_repository_resilience.apply()
    async def change_vfolder_ownership(
        self,
        vfolder_id: uuid.UUID,
        user_email: str,
    ) -> None:
        """
        Change ownership of a user vfolder to another user.
        Validates user exists with allowed host access, updates owner,
        and removes related invitations/permissions for the new owner.
        """
        # Step 1: Get target user info and their allowed hosts
        async with self._db.begin_readonly_session() as session:
            conn = await session.connection()
            j = sa.join(users, keypairs, users.c.uuid == keypairs.c.user)
            db_query = (
                sa.select(users.c.uuid, users.c.domain_name, keypairs.c.resource_policy)
                .select_from(j)
                .where((users.c.email == user_email) & (users.c.status == UserStatus.ACTIVE))
            )
            try:
                result = await conn.execute(db_query)
            except sa.exc.DataError as e:
                raise InvalidAPIParameters from e
            user_info = result.first()
            if user_info is None:
                raise UserNotFound()

            resource_policy_name = user_info.resource_policy
            result = await conn.execute(
                sa.select(keypair_resource_policies.c.allowed_vfolder_hosts).where(
                    keypair_resource_policies.c.name == resource_policy_name
                )
            )
            resource_policy_row = result.first()
            allowed_hosts_by_user = await get_allowed_vfolder_hosts_by_user(
                conn=conn,
                resource_policy=dict(resource_policy_row._mapping) if resource_policy_row else {},
                domain_name=user_info.domain_name,
                user_uuid=user_info.uuid,
            )

        # Step 2: Check vfolder host is accessible by new owner and get old owner
        async with self._db.begin_readonly_session() as session:
            conn = await session.connection()
            db_query = (
                sa.select(vfolders.c.host, vfolders.c.user)
                .select_from(vfolders)
                .where(
                    (vfolders.c.id == vfolder_id)
                    & (vfolders.c.ownership_type == VFolderOwnershipType.USER)
                )
            )
            row = (await conn.execute(db_query)).first()
            folder_host = row.host if row else None
            old_owner_uuid = row.user if row else None
        if folder_host not in allowed_hosts_by_user:
            raise VFolderOperationFailed(
                "User to migrate vfolder needs an access to the storage host."
            )

        # Step 3: Update vfolder owner. The folder moves into the new owner's personal
        # project, so the project column follows the user column.
        new_owner_project = await self.get_personal_project_id(user_info.uuid)

        async def _update() -> None:
            async with self._db.begin_session() as session:
                conn = await session.connection()
                update_query = (
                    sa.update(vfolders)
                    .values(user=user_info.uuid, group=new_owner_project)
                    .where(
                        (vfolders.c.id == vfolder_id)
                        & (vfolders.c.ownership_type == VFolderOwnershipType.USER)
                    )
                )
                await conn.execute(update_query)

        await execute_with_retry(_update)

        # Step 4: Delete related invitations and permissions for new owner
        async def _delete_related_rows() -> None:
            # Also clear what the new owner held from when they were an invitee; the
            # ownership below replaces it uncapped. Their legacy mount row is left
            # standing — accepting a later invitation reads it (BA-5277).
            async with self._v2_ops.write_ops() as w:
                # TODO: scope this purge. A user operation must not use in_global.
                await w.batch_purge_entities_in_global(
                    EntitySharePendingOfferBatchPurger(
                        entity_type=VFolderEntityType(),
                        entity_ids=[vfolder_id],
                        recipient_email=user_email,
                    )
                )
                held = await w.lookup_entity_id(
                    HeldShareLookup(
                        recipient=UserID(user_info.uuid), target=VFolderUUID(vfolder_id)
                    )
                )
                if held is not None:
                    await w.revoke_share(EntityShareRevokeUpdater(share_id=held))
                await w.unshare(new_owner_project, [VFolderUUID(vfolder_id)])

        await execute_with_retry(_delete_related_rows)

        # Step 5: Clean up old owner's RBAC records for this vfolder
        if old_owner_uuid is not None and old_owner_uuid != user_info.uuid:
            old_owner_project = await self.get_personal_project_id(old_owner_uuid)

            async def _transfer_rbac() -> None:
                async with self._v2_ops.write_ops() as w:
                    await w.transfer(
                        [old_owner_project], [new_owner_project], VFolderUUID(vfolder_id)
                    )

            await execute_with_retry(_transfer_rbac)
        else:

            async def _own_by_new_owner() -> None:
                async with self._v2_ops.write_ops() as w:
                    await w.transfer([], [new_owner_project], VFolderUUID(vfolder_id))

            await execute_with_retry(_own_by_new_owner)

    @vfolder_repository_resilience.apply()
    async def get_alive_agent_ids(
        self,
        resource_group: str | None = None,
    ) -> list[str]:
        """Get IDs of agents with ALIVE status, optionally filtered by scaling group."""
        async with self._db.begin_readonly_session() as session:
            conn = await session.connection()
            stmt = sa.select(agents.c.id).where(agents.c.status == AgentStatus.ALIVE)
            if resource_group is not None:
                stmt = stmt.where(agents.c.scaling == resource_group)
            result = await conn.execute(stmt)
            return [row.id for row in result.fetchall()]

    @vfolder_repository_resilience.apply()
    async def get_active_kernel_mount_names(self) -> set[str]:
        """Get mount names from all non-terminated kernels."""
        async with self._db.begin_readonly_session() as session:
            conn = await session.connection()
            stmt = sa.select(kernels.c.mounts).where(kernels.c.status != KernelStatus.TERMINATED)
            result = await conn.execute(stmt)
            mounted: set[str] = set()
            for row in result.fetchall():
                if row.mounts:
                    mounted.update(m[1] for m in row.mounts)
            return mounted
