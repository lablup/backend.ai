import asyncio
from typing import (
    Optional,
    cast,
)

import sqlalchemy as sa
from sqlalchemy.orm import contains_eager

from ai.backend.common.types import (
    VFolderHostPermission,
)
from ai.backend.manager.config import SharedConfig
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderInvitationRow,
    VFolderInvitationState,
    VFolderOwnershipType,
    VFolderPermissionRow,
    VFolderRow,
    VFolderStatusSet,
    ensure_host_permission_allowed,
    vfolder_status_map,
)
from ai.backend.manager.models.vfolder import VFolderPermission as VFolderMountPermission

from ..actions.invite import (
    AcceptInvitationAction,
    AcceptInvitationActionResult,
    InviteVFolderAction,
    InviteVFolderActionResult,
    LeaveInvitedVFolderAction,
    LeaveInvitedVFolderActionResult,
    ListInvitationAction,
    ListInvitationActionResult,
    RejectInvitationAction,
    RejectInvitationActionResult,
    UpdateInvitationAction,
    UpdateInvitationActionResult,
)
from ..exceptions import (
    Forbidden,
    InsufficientPrivilege,
    InternalServerError,
    InvalidParameter,
    ObjectNotFound,
    VFolderAlreadyExists,
    VFolderNotFound,
)
from ..types import VFolderInvitationInfo

# TODO: Detach privilege check from the service.
#       The service should only handle the business logic.
#       The privilege check should be done before calling the service.
#       Invite services should receive invitiation ids which are already checked.


class VFolderInviteService:
    _db: ExtendedAsyncSAEngine
    _shared_config: SharedConfig

    def __init__(self, db: ExtendedAsyncSAEngine, shared_config: SharedConfig) -> None:
        self._db = db
        self._shared_config = shared_config

    async def invite(self, action: InviteVFolderAction) -> InviteVFolderActionResult:
        async with self._db.begin_readonly_session() as db_session:
            query_vfolder = sa.select(VFolderRow).where(VFolderRow.id == action.vfolder_uuid)
            vfolder_row = await db_session.scalar(query_vfolder)
            vfolder_row = cast(VFolderRow, vfolder_row)

            inviter_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.user_uuid)
            )
            inviter_user_row = cast(UserRow, inviter_user_row)
            invitee_user_rows = await db_session.scalars(
                sa.select(UserRow).where(UserRow.uuid.in_(action.invitee_user_uuids))
            )
            invitee_user_rows = cast(list[UserRow], invitee_user_rows.all())
        if vfolder_row.name.startswith("."):
            raise Forbidden("Cannot share private dot-prefixed vfolders.")

        allowed_vfolder_types = await self._shared_config.get_vfolder_types()
        async with self._db.begin_session() as db_session:
            query_vfolder = sa.select(VFolderRow).where(VFolderRow.id == action.vfolder_uuid)
            vfolder_row = await db_session.scalar(query_vfolder)
            vfolder_row = cast(VFolderRow, vfolder_row)
            await ensure_host_permission_allowed(
                db_session.bind,
                vfolder_row.host,
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=action.user_uuid,
                resource_policy=action.keypair_resource_policy,
                domain_name=vfolder_row.domain_name,
                permission=VFolderHostPermission.INVITE_OTHERS,
            )

            # Prevent inviting user who already share the target folder.
            j = sa.join(
                VFolderPermissionRow, VFolderRow, VFolderRow.id == VFolderPermissionRow.vfolder
            )
            count_query = (
                sa.select(sa.func.count())
                .select_from(j)
                .where(
                    sa.and_(
                        sa.or_(
                            VFolderPermissionRow.user.in_(action.invitee_user_uuids),
                            VFolderRow.user.in_(action.invitee_user_uuids),
                        ),
                        VFolderPermissionRow.vfolder == action.vfolder_uuid,
                    )
                )
            )
            count = await db_session.scalar(count_query)
            if count > 0:
                raise VFolderAlreadyExists(
                    "Invitation to this VFolder already sent out to target user"
                )

            # Create invitation.
            invited_ids = []
            inviter = inviter_user_row.email
            for invitee in set([row.email for row in invitee_user_rows]):
                # Do not create invitation if already exists.
                query = (
                    sa.select(sa.func.count())
                    .select_from(VFolderInvitationRow)
                    .where(
                        (VFolderInvitationRow.inviter == inviter)
                        & (VFolderInvitationRow.invitee == invitee)
                        & (VFolderInvitationRow.vfolder == action.vfolder_uuid)
                        & (VFolderInvitationRow.state == VFolderInvitationState.PENDING),
                    )
                )
                result = await db_session.scalar(query)
                if result > 0:
                    continue

                # TODO: insert multiple values with one query.
                #       insert().values([{}, {}, ...]) does not work:
                #       sqlalchemy.exc.CompileError: The 'default' dialect with current
                #       database version settings does not support in-place multirow
                #       inserts.
                query = sa.insert(
                    VFolderInvitationRow,
                    {
                        "permission": action.mount_permission,
                        "vfolder": action.vfolder_uuid,
                        "inviter": inviter,
                        "invitee": invitee,
                        "state": VFolderInvitationState.PENDING,
                    },
                )
                try:
                    await db_session.execute(query)
                    invited_ids.append(invitee)
                except sa.exc.DataError:
                    pass
        return InviteVFolderActionResult(
            vfolder_uuid=action.vfolder_uuid, invitation_ids=invited_ids
        )

    async def accept_invitation(
        self, action: AcceptInvitationAction
    ) -> AcceptInvitationActionResult:
        async with self._db.begin_session() as db_session:
            # Get invitation.
            query = sa.select(VFolderInvitationRow).where(
                sa.and_(
                    VFolderInvitationRow.id == action.invitation_id,
                    VFolderInvitationRow.state == VFolderInvitationState.PENDING,
                )
            )
            invitation_row = await db_session.scalar(query)
            invitation_row = cast(VFolderInvitationRow, invitation_row)
            if invitation_row is None:
                raise ObjectNotFound()

            # Get target user.
            query = sa.select(UserRow).where(UserRow.email == invitation_row.invitee)
            user_row = await db_session.scalar(query)
            user_row = cast(UserRow, user_row)

            # Get target virtual folder.
            query = sa.select(VFolderRow).where(VFolderRow.id == invitation_row.vfolder)
            target_vfolder = await db_session.scalar(query)
            target_vfolder = cast(Optional[VFolderRow], target_vfolder)
            if target_vfolder is None:
                raise VFolderNotFound

            # Prevent accepting vfolder with duplicated name.
            j = sa.join(
                VFolderRow,
                VFolderPermissionRow,
                VFolderRow.id == VFolderPermissionRow.vfolder,
                isouter=True,
            )
            query = (
                sa.select(sa.func.count())
                .select_from(j)
                .where(
                    sa.and_(
                        sa.or_(
                            VFolderRow.user == user_row.uuid,
                            VFolderPermissionRow.user == user_row.uuid,
                        ),
                        VFolderRow.name == target_vfolder.name,
                        VFolderRow.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE]),
                    )
                )
            )
            result = await db_session.scalar(query)
            if result > 0:
                raise VFolderAlreadyExists

            # Create permission relation between the vfolder and the invitee.
            query = sa.insert(
                VFolderPermissionRow,
                {
                    "permission": VFolderMountPermission(invitation_row.permission),
                    "vfolder": invitation_row.vfolder,
                    "user": user_row.uuid,
                },
            )
            await db_session.execute(query)

            # Clear used invitation.
            query = (
                sa.update(VFolderInvitationRow)
                .where(VFolderInvitationRow.id == action.invitation_id)
                .values(state=VFolderInvitationState.ACCEPTED)
            )
            await db_session.execute(query)
        return AcceptInvitationActionResult(action.invitation_id)

    async def reject_invitation(
        self,
        action: RejectInvitationAction,
    ) -> RejectInvitationActionResult:
        try:
            async with self._db.begin_session() as db_session:
                query = sa.select(VFolderInvitationRow).where(
                    (VFolderInvitationRow.id == action.invitation_id)
                    & (VFolderInvitationRow.state == VFolderInvitationState.PENDING),
                )
                invitation_row = await db_session.scalar(query)
                invitation_row = cast(Optional[VFolderInvitationRow], invitation_row)
                requester_query = sa.select(UserRow).where(
                    UserRow.uuid == action.requester_user_uuid
                )
                user_row = await db_session.scalar(requester_query)
                user_row = cast(UserRow, user_row)
                if invitation_row is None:
                    raise ObjectNotFound("vfolder invitation")
                if user_row.email == invitation_row.inviter:
                    state = VFolderInvitationState.CANCELED
                elif user_row.email == invitation_row.invitee:
                    state = VFolderInvitationState.REJECTED
                else:
                    raise Forbidden("Cannot change other user's invitaiton")
                query = (
                    sa.update(VFolderInvitationRow)
                    .values(state=state)
                    .where(VFolderInvitationRow.id == action.invitation_id)
                )
                await db_session.execute(query)
        except sa.exc.IntegrityError as e:
            raise InternalServerError(f"integrity error: {e}")
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception as e:
            raise InternalServerError(f"unexpected error: {e}")
        return RejectInvitationActionResult(action.invitation_id)

    async def update_invitation(
        self, action: UpdateInvitationAction
    ) -> UpdateInvitationActionResult:
        inv_id = action.invitation_id
        async with self._db.begin_session() as db_session:
            user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.requester_user_uuid)
            )
            user_row = cast(UserRow, user_row)
            query = (
                sa.update(VFolderInvitationRow)
                .values(permission=action.mount_permission)
                .where(
                    sa.and_(
                        VFolderInvitationRow.id == inv_id,
                        VFolderInvitationRow.inviter == user_row.email,
                        VFolderInvitationRow.state == VFolderInvitationState.PENDING,
                    )
                )
            )
            await db_session.execute(query)
        return UpdateInvitationActionResult(inv_id)

    async def list_invitation(self, action: ListInvitationAction) -> ListInvitationActionResult:
        async with self._db.begin_session() as db_session:
            user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.requester_user_uuid)
            )
            user_row = cast(UserRow, user_row)
            j = sa.join(
                VFolderInvitationRow, VFolderRow, VFolderInvitationRow.vfolder == VFolderRow.id
            )
            query = (
                sa.select(VFolderInvitationRow)
                .select_from(j)
                .where(
                    sa.and_(
                        VFolderInvitationRow.invitee == user_row.email,
                        VFolderInvitationRow.state == VFolderInvitationState.PENDING,
                    )
                )
                .options(
                    contains_eager(VFolderInvitationRow.vfolder_row),
                )
            )
            invitations_rows = await db_session.scalars(query)
            invitations_rows = cast(list[VFolderInvitationRow], invitations_rows.all())
        invs_info: list[VFolderInvitationInfo] = []
        for inv in invitations_rows:
            # TODO: Check query result
            info = VFolderInvitationInfo(
                id=inv.id,
                vfolder_id=inv.vfolder,
                vfolder_name=inv.vfolder_row.name,
                invitee_user_email=inv.invitee,
                inviter_user_email=inv.inviter,
                mount_permission=inv.permission,
                created_at=inv.created_at,
                modified_at=inv.modified_at,
                status=inv.state,
            )
            invs_info.append(info)
        return ListInvitationActionResult(
            requester_user_uuid=action.requester_user_uuid, info=invs_info
        )

    async def leave_invited_vfolder(
        self, action: LeaveInvitedVFolderAction
    ) -> LeaveInvitedVFolderActionResult:
        async with self._db.begin_session() as db_session:
            vfolder_row = await db_session.scalar(
                sa.select(VFolderRow).where(VFolderRow.id == action.vfolder_uuid)
            )
            vfolder_row = cast(VFolderRow, vfolder_row)
            requester_user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == action.requester_user_uuid)
            )
            requester_user_row = cast(UserRow, requester_user_row)
            if vfolder_row.ownership_type == VFolderOwnershipType.GROUP:
                raise InvalidParameter("Cannot leave a group vfolder.")

            if action.shared_user_uuid:
                # Allow only superadmin to leave the shared vfolder of others.
                if (action.requester_user_uuid != action.shared_user_uuid) and (
                    requester_user_row.role != UserRole.SUPERADMIN
                ):
                    raise InsufficientPrivilege("Insufficient permission.")
                user_uuid = action.shared_user_uuid
            else:
                user_uuid = action.requester_user_uuid

            query = (
                sa.delete(VFolderPermissionRow)
                .where(VFolderPermissionRow.vfolder == action.vfolder_uuid)
                .where(VFolderPermissionRow.user == user_uuid)
            )
            await db_session.execute(query)
        return LeaveInvitedVFolderActionResult(vfolder_row.id)
