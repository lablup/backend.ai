"""What a customized image records about the user it was committed for.

Covers what the scan writes — the creator column and the graph edge to that user's
personal project — and the two readers that used to parse the owner label: the
per-user image quota and the availability check a session start makes.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, override
from uuid import UUID, uuid4

import aiohttp
import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import (
    CONTAINER_REGISTRY_ENTITY_TYPE,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import (
    PROJECT_ENTITY_TYPE,
    PROJECT_SCOPE_TYPE,
    ProjectID,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.docker import LabelName
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.container_registry.base import (
    BaseContainerRegistry,
    RescanCounts,
    all_updates,
    rescan_counts,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.image.types import ImageData, ImageStatus, ImageType
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageAliasRow, ImageIdentifier, ImageRow
from ai.backend.manager.models.image.creators import ImageCreator
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.manager.repositories.session.db_source.db_source import SessionDBSource
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

DOMAIN_NAME = "test-domain"
REGISTRY_NAME = "cr.test.io"
REGISTRY_PROJECT = "stable"
USER_RESOURCE_POLICY_NAME = "test-user-policy"
PROJECT_RESOURCE_POLICY_NAME = "test-project-policy"
KEYPAIR_RESOURCE_POLICY_NAME = "test-keypair-policy"

# ORM cluster registration: string relationships resolve against the registry when
# mappers configure, so rows reachable only through them are kept live here.
_ORM_CLUSTER = (
    AgentRow,
    AssociationContainerRegistriesGroupsRow,
    ImageAliasRow,
    KeyPairRow,
    ResourceGroupForDomainRow,
)


class _FakeRegistryScanner(BaseContainerRegistry):
    """The rescan commit alone; nothing here reaches the registry over HTTP."""

    @override
    async def fetch_repositories(self, sess: aiohttp.ClientSession) -> AsyncIterator[str]:
        names: list[str] = []
        for name in names:
            yield name
        raise NotImplementedError


class TestImageOwnershipGraph:
    # -- fixtures ----------------------------------------------------------------------

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                AssocGroupUserRow,
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
                ImageRow,
                ImageAliasRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                EntityMembershipFieldRow,
                ScopeBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def domain_id(self, db_with_cleanup: ExtendedAsyncSAEngine) -> DomainID:
        domain_id = DomainID(uuid4())
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                DomainRow(
                    id=domain_id,
                    name=DOMAIN_NAME,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[REGISTRY_NAME],
                    dotfiles=b"\x90",
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=USER_RESOURCE_POLICY_NAME,
                    max_vfolder_count=0,
                    max_quota_scope_size=0,
                    max_session_count_per_model_session=0,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=PROJECT_RESOURCE_POLICY_NAME,
                    max_vfolder_count=0,
                    max_quota_scope_size=0,
                    max_network_count=0,
                )
            )
            await sess.commit()
        return domain_id

    @pytest.fixture
    async def registry_id(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain_id: DomainID
    ) -> ContainerRegistryID:
        registry_id = ContainerRegistryID(uuid4())
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url=f"https://{REGISTRY_NAME}",
                    registry_name=REGISTRY_NAME,
                    type=ContainerRegistryType.DOCKER,
                    project=REGISTRY_PROJECT,
                    is_global=True,
                )
            )
            await VirtualEntitySeeder().get_or_create_node(
                sess, CONTAINER_REGISTRY_ENTITY_TYPE, registry_id
            )
            await sess.commit()
        return registry_id

    # -- helpers -----------------------------------------------------------------------

    async def _create_user(
        self, db: ExtendedAsyncSAEngine, domain_id: DomainID, email: str
    ) -> UserID:
        user_id = UserID(uuid4())
        async with db.begin_session() as sess:
            sess.add(
                UserRow(
                    uuid=user_id,
                    username=email,
                    email=email,
                    password=PasswordInfo(
                        password="dummy",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=600_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    domain_name=DOMAIN_NAME,
                    domain_id=domain_id,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    resource_policy=USER_RESOURCE_POLICY_NAME,
                )
            )
            await sess.commit()
        return user_id

    async def _create_personal_project(
        self, db: ExtendedAsyncSAEngine, user_id: UserID, name: str
    ) -> ProjectID:
        project_id = ProjectID(uuid4())
        async with db.begin_session() as sess:
            sess.add(
                ProjectRow(
                    id=project_id,
                    name=name,
                    domain_name=DOMAIN_NAME,
                    is_active=True,
                    type=ProjectType.PERSONAL,
                    creator_id=user_id,
                    resource_policy=PROJECT_RESOURCE_POLICY_NAME,
                )
            )
            await VirtualEntitySeeder().get_or_create_node(sess, PROJECT_ENTITY_TYPE, project_id)
            await sess.commit()
        return project_id

    async def _create_image(
        self,
        db: ExtendedAsyncSAEngine,
        registry_id: ContainerRegistryID,
        tag: str,
        *,
        owner_user_id: UserID | None = None,
        created_in_project_id: ProjectID | None = None,
        customized: bool | None = None,
        status: ImageStatus = ImageStatus.ALIVE,
    ) -> tuple[ImageID, str]:
        canonical = f"{REGISTRY_NAME}/{REGISTRY_PROJECT}/python:{tag}"
        async with V2DBOpsProvider(db).write_ops() as w:
            created = await w.atomic_create_entities([
                ImageCreator(
                    name=canonical,
                    project=REGISTRY_PROJECT,
                    architecture="x86_64",
                    registry_id=registry_id,
                    registry=REGISTRY_NAME,
                    image="python",
                    tag=tag,
                    config_digest=f"sha256:{uuid4().hex}",
                    size_bytes=1000,
                    type=ImageType.COMPUTE,
                    labels=self._customized_labels(owner_user_id),
                    status=status,
                    customized=customized if customized is not None else owner_user_id is not None,
                    creator_id=owner_user_id,
                    created_in_project_id=created_in_project_id,
                )
            ])
        image_id = created[0].id
        if status is not ImageStatus.ALIVE:
            async with db.begin_session() as sess:
                await sess.execute(
                    sa.update(ImageRow).where(ImageRow.id == image_id).values(status=status)
                )
                await sess.commit()
        return image_id, canonical

    def _customized_labels(self, owner_user_id: UserID | None) -> dict[str, Any]:
        if owner_user_id is None:
            return {}
        return {
            LabelName.CUSTOMIZED_OWNER.value: f"user:{owner_user_id}",
            LabelName.CUSTOMIZED_NAME.value: "my-image",
        }

    async def _kind_and_creator(
        self, db: ExtendedAsyncSAEngine, image_id: ImageID
    ) -> tuple[bool, UUID | None]:
        async with db.begin_readonly_session() as sess:
            row = (
                await sess.execute(
                    sa.select(ImageRow.customized, ImageRow.creator_id).where(
                        ImageRow.id == image_id
                    )
                )
            ).one()
            return row.customized, row.creator_id

    async def _owning_projects(self, db: ExtendedAsyncSAEngine, image_id: ImageID) -> list[UUID]:
        async with V2DBOpsProvider(db).read_ops() as r:
            return list(await r.scopes_owning(PROJECT_SCOPE_TYPE, image_id))

    async def _commit_rescan(
        self,
        db: ExtendedAsyncSAEngine,
        registry_id: ContainerRegistryID,
        updates: dict[ImageIdentifier, dict[str, Any]],
    ) -> list[ImageData]:
        async with db.begin_readonly_session() as sess:
            registry_row = await sess.get(ContainerRegistryRow, registry_id)
            assert registry_row is not None
            sess.expunge(registry_row)
        scanner = _FakeRegistryScanner(db, REGISTRY_NAME, registry_row)
        updates_token = all_updates.set(updates)
        counts_token = rescan_counts.set(RescanCounts())
        try:
            return await scanner.commit_rescan_result()
        finally:
            all_updates.reset(updates_token)
            rescan_counts.reset(counts_token)

    def _scan_payload(self, owner_user_id: UserID | None) -> dict[str, Any]:
        return {
            "config_digest": f"sha256:{uuid4().hex}",
            "size_bytes": 2000,
            "labels": self._customized_labels(owner_user_id),
        }

    # -- the per-user image quota ------------------------------------------------------

    async def test_quota_counts_what_the_personal_project_owns(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        for tag in ("a", "b"):
            await self._create_image(
                db_with_cleanup,
                registry_id,
                tag,
                owner_user_id=user_id,
            )

        db_source = SessionDBSource(db_with_cleanup, DBOpsProvider(db_with_cleanup))

        assert await db_source.get_customized_image_count(user_id) == 2

    async def test_quota_ignores_what_another_project_owns(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        other_id = await self._create_user(db_with_cleanup, domain_id, "other@test.io")
        await self._create_image(
            db_with_cleanup,
            registry_id,
            "a",
            owner_user_id=other_id,
        )

        db_source = SessionDBSource(db_with_cleanup, DBOpsProvider(db_with_cleanup))

        assert await db_source.get_customized_image_count(user_id) == 0

    async def test_quota_ignores_a_deleted_image(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        await self._create_image(
            db_with_cleanup,
            registry_id,
            "a",
            owner_user_id=user_id,
            status=ImageStatus.DELETED,
        )

        db_source = SessionDBSource(db_with_cleanup, DBOpsProvider(db_with_cleanup))

        assert await db_source.get_customized_image_count(user_id) == 0

    async def test_quota_ignores_an_image_that_is_not_customized(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        await self._create_image(db_with_cleanup, registry_id, "a")

        db_source = SessionDBSource(db_with_cleanup, DBOpsProvider(db_with_cleanup))

        assert await db_source.get_customized_image_count(user_id) == 0

    # -- the availability check --------------------------------------------------------

    async def test_the_owning_user_reaches_their_image(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        image_id, _ = await self._create_image(
            db_with_cleanup,
            registry_id,
            "a",
            owner_user_id=user_id,
        )

        await ScheduleDBSource(
            db_with_cleanup, ReconcileOpsProvider(db_with_cleanup)
        ).check_available_image(image_id, DOMAIN_NAME, user_id)

    async def test_another_users_image_reads_as_absent(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        other_id = await self._create_user(db_with_cleanup, domain_id, "other@test.io")
        image_id, _ = await self._create_image(
            db_with_cleanup,
            registry_id,
            "a",
            owner_user_id=other_id,
        )

        with pytest.raises(ImageNotFound):
            await ScheduleDBSource(
                db_with_cleanup, ReconcileOpsProvider(db_with_cleanup)
            ).check_available_image(image_id, DOMAIN_NAME, user_id)

    async def test_an_image_that_is_not_customized_is_reachable_by_anyone(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        image_id, _ = await self._create_image(db_with_cleanup, registry_id, "a")

        await ScheduleDBSource(
            db_with_cleanup, ReconcileOpsProvider(db_with_cleanup)
        ).check_available_image(image_id, DOMAIN_NAME, user_id)

    async def test_a_customized_image_with_no_creator_is_reachable_by_nobody(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        image_id, _ = await self._create_image(db_with_cleanup, registry_id, "a", customized=True)

        with pytest.raises(ImageNotFound):
            await ScheduleDBSource(
                db_with_cleanup, ReconcileOpsProvider(db_with_cleanup)
            ).check_available_image(image_id, DOMAIN_NAME, user_id)

    async def test_purging_the_creator_leaves_the_image_reachable_by_nobody(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        owner_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        onlooker_id = await self._create_user(db_with_cleanup, domain_id, "other@test.io")
        image_id, _ = await self._create_image(
            db_with_cleanup, registry_id, "a", owner_user_id=owner_id
        )
        async with db_with_cleanup.begin_session() as sess:
            await sess.execute(sa.delete(UserRow).where(UserRow.uuid == owner_id))
            await sess.commit()

        db_source = ScheduleDBSource(db_with_cleanup, ReconcileOpsProvider(db_with_cleanup))

        with pytest.raises(ImageNotFound):
            await db_source.check_available_image(image_id, DOMAIN_NAME, onlooker_id)

    # -- what the scan writes ----------------------------------------------------------

    async def test_a_scanned_customized_image_joins_its_personal_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        project_id = await self._create_personal_project(db_with_cleanup, user_id, "owner")
        canonical = f"{REGISTRY_NAME}/{REGISTRY_PROJECT}/python:a"

        scanned = await self._commit_rescan(
            db_with_cleanup,
            registry_id,
            {ImageIdentifier(canonical, "x86_64"): self._scan_payload(user_id)},
        )

        assert [(image.customized, image.creator_id) for image in scanned] == [(True, user_id)]
        assert await self._owning_projects(db_with_cleanup, scanned[0].id) == [project_id]

    async def test_a_scanned_image_stays_unowned_without_a_personal_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        canonical = f"{REGISTRY_NAME}/{REGISTRY_PROJECT}/python:a"

        scanned = await self._commit_rescan(
            db_with_cleanup,
            registry_id,
            {ImageIdentifier(canonical, "x86_64"): self._scan_payload(user_id)},
        )

        assert [(image.customized, image.creator_id) for image in scanned] == [(True, user_id)]
        assert await self._owning_projects(db_with_cleanup, scanned[0].id) == []

    async def test_rescanning_an_image_on_file_leaves_the_graph_alone(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        await self._create_personal_project(db_with_cleanup, user_id, "owner")
        image_id, canonical = await self._create_image(
            db_with_cleanup, registry_id, "a", owner_user_id=user_id
        )

        await self._commit_rescan(
            db_with_cleanup,
            registry_id,
            {ImageIdentifier(canonical, "x86_64"): self._scan_payload(user_id)},
        )

        assert await self._owning_projects(db_with_cleanup, image_id) == []

    async def test_rescanning_refreshes_the_kind_and_the_creator_from_the_labels(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        user_id = await self._create_user(db_with_cleanup, domain_id, "owner@test.io")
        image_id, canonical = await self._create_image(db_with_cleanup, registry_id, "a")

        await self._commit_rescan(
            db_with_cleanup,
            registry_id,
            {ImageIdentifier(canonical, "x86_64"): self._scan_payload(user_id)},
        )

        assert await self._kind_and_creator(db_with_cleanup, image_id) == (True, user_id)

    async def test_rescanning_an_unreadable_owner_label_marks_it_customized_alone(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain_id: DomainID,
        registry_id: ContainerRegistryID,
    ) -> None:
        image_id, canonical = await self._create_image(db_with_cleanup, registry_id, "a")
        payload = self._scan_payload(None)
        payload["labels"] = {LabelName.CUSTOMIZED_OWNER.value: "user:not-a-uuid"}

        await self._commit_rescan(
            db_with_cleanup,
            registry_id,
            {ImageIdentifier(canonical, "x86_64"): payload},
        )

        assert await self._kind_and_creator(db_with_cleanup, image_id) == (True, None)
