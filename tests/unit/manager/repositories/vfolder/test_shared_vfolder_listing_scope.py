"""Tests for `VfolderRepository.list_shared_vfolder_permissions` requester scoping.

The listing behind `GET /folders/_/shared` must only hand back the sharing entries the
requester is party to: the share is granted to them, or it stands on a folder they own,
created, or reach through their project membership. Everything else — including the
grantee's UUID and e-mail — must stay out of the result. Omitting the requester lists
every entry, which is the superadmin/monitor path.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.permission.types import (
    EntityType as PermissionEntityType,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as PermissionScopeType,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionRow,
    VFolderRow,
)
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.testutils.db import with_tables

DOMAIN_NAME_FIXED = "test-domain-shared-scope"


def _password() -> PasswordInfo:
    return PasswordInfo(
        password="dummy",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=600_000,
        salt_size=32,
    )


@dataclass(frozen=True)
class _Fixture:
    """The ids seeded for one scoping scenario.

    The requester is a member of `project` and a stranger to `other_project`. Each
    vfolder carries exactly one sharing entry, so a folder id identifies its entry.
    """

    requester: UUID
    # folders the requester is party to, and the e-mail each one's share is granted to
    granted_to_requester: UUID
    owned_by_requester: UUID
    created_by_requester: UUID
    in_requester_project: UUID
    # folders the requester is a stranger to
    unrelated: UUID
    in_other_project: UUID

    requester_email: str
    stranger_grantee_emails: tuple[str, ...]

    @property
    def visible_vfolder_ids(self) -> set[UUID]:
        return {
            self.granted_to_requester,
            self.owned_by_requester,
            self.created_by_requester,
            self.in_requester_project,
        }

    @property
    def hidden_vfolder_ids(self) -> set[UUID]:
        return {self.unrelated, self.in_other_project}


class TestListSharedVFolderPermissionsScope:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
                VFolderPermissionRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def seeded(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[_Fixture, None]:
        user_policy = f"user-{uuid4().hex[:8]}"
        project_policy = f"proj-{uuid4().hex[:8]}"
        project = uuid4()
        other_project = uuid4()
        requester = uuid4()
        stranger = uuid4()
        grantees = {name: uuid4() for name in ("a", "b", "c", "d", "e")}
        requester_email = f"requester-{requester.hex[:8]}@example.com"
        grantee_emails = {
            name: f"grantee-{name}-{grantee.hex[:8]}@example.com"
            for name, grantee in grantees.items()
        }

        def _user(user_uuid: UUID, email: str) -> UserRow:
            return UserRow(
                uuid=user_uuid,
                username=f"u_{user_uuid.hex[:8]}",
                email=email,
                password=_password(),
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=DOMAIN_NAME_FIXED,
                role=UserRole.USER,
                resource_policy=user_policy,
            )

        def _project_row(group_id: UUID, name: str) -> GroupRow:
            return GroupRow(
                id=group_id,
                name=name,
                domain_name=DOMAIN_NAME_FIXED,
                resource_policy=project_policy,
                description="",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                type=ProjectType.GENERAL,
            )

        def _user_vfolder(vfolder_id: UUID, owner: UUID, creator_id: UUID) -> VFolderRow:
            return VFolderRow(
                id=vfolder_id,
                name=f"vf-{vfolder_id.hex[:8]}",
                host="local",
                domain_name=DOMAIN_NAME_FIXED,
                quota_scope_id=f"user:{owner}",
                ownership_type=VFolderOwnershipType.USER,
                user=owner,
                group=None,
                creator=f"u_{creator_id.hex[:8]}@example.com",
                creator_id=creator_id,
                unmanaged_path=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )

        def _project_vfolder(vfolder_id: UUID, group_id: UUID, creator_id: UUID) -> VFolderRow:
            return VFolderRow(
                id=vfolder_id,
                name=f"vf-{vfolder_id.hex[:8]}",
                host="local",
                domain_name=DOMAIN_NAME_FIXED,
                quota_scope_id=f"project:{group_id}",
                ownership_type=VFolderOwnershipType.GROUP,
                user=None,
                group=group_id,
                creator=f"u_{creator_id.hex[:8]}@example.com",
                creator_id=creator_id,
                unmanaged_path=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
            )

        def _share(vfolder_id: UUID, grantee: UUID) -> VFolderPermissionRow:
            return VFolderPermissionRow(
                vfolder=vfolder_id,
                user=grantee,
                permission=VFolderPermission.READ_ONLY,
            )

        granted_to_requester = uuid4()
        owned_by_requester = uuid4()
        created_by_requester = uuid4()
        in_requester_project = uuid4()
        unrelated = uuid4()
        in_other_project = uuid4()

        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                DomainRow(
                    name=DOMAIN_NAME_FIXED,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=user_policy,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=5,
                )
            )
            await sess.flush()

            sess.add(_project_row(project, f"proj-{project.hex[:8]}"))
            sess.add(_project_row(other_project, f"other-{other_project.hex[:8]}"))
            sess.add(_user(requester, requester_email))
            sess.add(_user(stranger, f"stranger-{stranger.hex[:8]}@example.com"))
            for name, grantee in grantees.items():
                sess.add(_user(grantee, grantee_emails[name]))
            await sess.flush()

            # The requester belongs to `project` only.
            sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(project),
                    entity_type=PermissionEntityType.USER,
                    entity_id=str(requester),
                )
            )

            sess.add(_user_vfolder(granted_to_requester, owner=stranger, creator_id=stranger))
            sess.add(_user_vfolder(owned_by_requester, owner=requester, creator_id=stranger))
            sess.add(_user_vfolder(created_by_requester, owner=stranger, creator_id=requester))
            sess.add(_project_vfolder(in_requester_project, project, creator_id=stranger))
            sess.add(_user_vfolder(unrelated, owner=stranger, creator_id=stranger))
            sess.add(_project_vfolder(in_other_project, other_project, creator_id=stranger))
            await sess.flush()

            sess.add(_share(granted_to_requester, requester))
            sess.add(_share(owned_by_requester, grantees["a"]))
            sess.add(_share(created_by_requester, grantees["b"]))
            sess.add(_share(in_requester_project, grantees["c"]))
            sess.add(_share(unrelated, grantees["d"]))
            sess.add(_share(in_other_project, grantees["e"]))
            await sess.flush()

        yield _Fixture(
            requester=requester,
            granted_to_requester=granted_to_requester,
            owned_by_requester=owned_by_requester,
            created_by_requester=created_by_requester,
            in_requester_project=in_requester_project,
            unrelated=unrelated,
            in_other_project=in_other_project,
            requester_email=requester_email,
            stranger_grantee_emails=(grantee_emails["d"], grantee_emails["e"]),
        )

    async def test_requester_sees_every_share_they_are_party_to(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        """Granted to them, owned, created, or reached through their project."""
        repo = VfolderRepository(db_with_cleanup)

        rows = await repo.list_shared_vfolder_permissions(requester_id=seeded.requester)

        assert {row["vfolder_id"] for row in rows} == seeded.visible_vfolder_ids

    async def test_unrelated_shares_are_hidden(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        """A stranger's share leaks neither the folder nor the grantee's UUID or e-mail."""
        repo = VfolderRepository(db_with_cleanup)

        rows = await repo.list_shared_vfolder_permissions(requester_id=seeded.requester)

        listed_vfolder_ids = {row["vfolder_id"] for row in rows}
        assert not (listed_vfolder_ids & seeded.hidden_vfolder_ids)
        listed_emails = {row["email"] for row in rows}
        for email in seeded.stranger_grantee_emails:
            assert email not in listed_emails

    async def test_membership_in_another_project_does_not_widen_the_listing(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        """The project folder the requester does not belong to stays hidden."""
        repo = VfolderRepository(db_with_cleanup)

        rows = await repo.list_shared_vfolder_permissions(requester_id=seeded.requester)

        assert seeded.in_other_project not in {row["vfolder_id"] for row in rows}
        assert seeded.in_requester_project in {row["vfolder_id"] for row in rows}

    async def test_omitting_the_requester_lists_every_entry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        """The superadmin/monitor path names no requester and is left unbounded."""
        repo = VfolderRepository(db_with_cleanup)

        rows = await repo.list_shared_vfolder_permissions()

        assert {row["vfolder_id"] for row in rows} == (
            seeded.visible_vfolder_ids | seeded.hidden_vfolder_ids
        )

    async def test_vfolder_id_filter_still_honors_the_requester_bound(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        """Naming a stranger's folder does not reveal its share."""
        repo = VfolderRepository(db_with_cleanup)

        rows = await repo.list_shared_vfolder_permissions(
            vfolder_id=seeded.unrelated,
            requester_id=seeded.requester,
        )

        assert rows == []

    async def test_vfolder_id_filter_returns_the_entry_the_requester_holds(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        repo = VfolderRepository(db_with_cleanup)

        rows = await repo.list_shared_vfolder_permissions(
            vfolder_id=seeded.granted_to_requester,
            requester_id=seeded.requester,
        )

        assert len(rows) == 1
        assert rows[0]["vfolder_id"] == seeded.granted_to_requester
        assert rows[0]["email"] == seeded.requester_email

    async def test_vfolder_id_filter_without_a_requester_returns_the_entry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        seeded: _Fixture,
    ) -> None:
        """The unbounded path keeps filtering by folder as before."""
        repo = VfolderRepository(db_with_cleanup)

        rows = await repo.list_shared_vfolder_permissions(vfolder_id=seeded.unrelated)

        assert len(rows) == 1
        assert rows[0]["vfolder_id"] == seeded.unrelated
