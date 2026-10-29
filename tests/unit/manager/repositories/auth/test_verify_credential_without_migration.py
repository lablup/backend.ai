"""Tests for ``AuthRepository.check_credential_without_migration`` against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.hasher.factory import compare_to_hashed_password
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFixtureData

_PASSWORD = "test_password"


def _password_info(password: str) -> PasswordInfo:
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


@dataclass(frozen=True)
class _Credential:
    domain_name: DomainName
    email: str
    user_uuid: uuid.UUID


class TestCheckCredentialWithoutMigration:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                ResourceGroupForDomainRow,
                ResourceGroupForProjectRow,
                ResourceGroupForKeypairsRow,
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
                VirtualEntityRow,
                EntityMembershipRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def auth_repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> AuthRepository:
        return AuthRepository(
            db=db_with_cleanup,
            v2_ops_provider=V2DBOpsProvider(db_with_cleanup),
            key_provider_pool=KeyProviderPool(
                providers=[], write_provider_type=KeyProviderType.PLAIN
            ),
        )

    async def _add_domain(self, db: ExtendedAsyncSAEngine) -> DomainFixtureData:
        domain = DomainFixtureData(
            domain_name=DomainName(f"domain-{uuid.uuid4().hex[:8]}"),
            domain_id=DomainID(uuid.uuid4()),
        )
        async with db.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain.domain_id,
                    name=domain.domain_name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
        return domain

    @pytest.fixture
    async def domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> DomainFixtureData:
        return await self._add_domain(db_with_cleanup)

    @pytest.fixture
    async def other_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> DomainFixtureData:
        return await self._add_domain(db_with_cleanup)

    @pytest.fixture
    async def user_resource_policy_name(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[str, None]:
        name = f"user-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
        yield name

    async def _add_user(
        self,
        db: ExtendedAsyncSAEngine,
        domain: DomainFixtureData,
        resource_policy: str,
        password: PasswordInfo | None,
    ) -> _Credential:
        user_uuid = uuid.uuid4()
        email = f"user-{user_uuid.hex[:8]}@example.com"
        async with db.begin_session() as db_sess:
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=email,
                    email=email,
                    password=password,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    domain_name=domain.domain_name,
                    domain_id=domain.domain_id,
                    role=UserRole.USER,
                    resource_policy=resource_policy,
                )
            )
        return _Credential(domain_name=domain.domain_name, email=email, user_uuid=user_uuid)

    @pytest.fixture
    async def user_with_password(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain: DomainFixtureData,
        user_resource_policy_name: str,
    ) -> _Credential:
        return await self._add_user(
            db_with_cleanup,
            domain,
            user_resource_policy_name,
            _password_info(_PASSWORD),
        )

    @pytest.fixture
    async def user_without_password(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain: DomainFixtureData,
        user_resource_policy_name: str,
    ) -> _Credential:
        return await self._add_user(db_with_cleanup, domain, user_resource_policy_name, None)

    async def test_returns_the_user_and_the_stored_hash_for_a_matching_credential(
        self,
        auth_repository: AuthRepository,
        user_with_password: _Credential,
    ) -> None:
        credential = await auth_repository.check_credential_without_migration(
            user_with_password.domain_name, user_with_password.email, _password_info(_PASSWORD)
        )

        assert credential.user_id == user_with_password.user_uuid
        assert compare_to_hashed_password(_PASSWORD, credential.hashed_password)

    async def test_rejects_a_wrong_password(
        self,
        auth_repository: AuthRepository,
        user_with_password: _Credential,
    ) -> None:
        with pytest.raises(AuthorizationFailed):
            await auth_repository.check_credential_without_migration(
                user_with_password.domain_name,
                user_with_password.email,
                _password_info("wrong_password"),
            )

    async def test_rejects_an_unknown_email(
        self,
        auth_repository: AuthRepository,
        user_with_password: _Credential,
    ) -> None:
        with pytest.raises(AuthorizationFailed):
            await auth_repository.check_credential_without_migration(
                user_with_password.domain_name, "nobody@example.com", _password_info(_PASSWORD)
            )

    async def test_rejects_the_email_under_another_domain(
        self,
        auth_repository: AuthRepository,
        user_with_password: _Credential,
        other_domain: DomainFixtureData,
    ) -> None:
        with pytest.raises(AuthorizationFailed):
            await auth_repository.check_credential_without_migration(
                other_domain.domain_name, user_with_password.email, _password_info(_PASSWORD)
            )

    async def test_rejects_a_user_without_a_password(
        self,
        auth_repository: AuthRepository,
        user_without_password: _Credential,
    ) -> None:
        with pytest.raises(AuthorizationFailed):
            await auth_repository.check_credential_without_migration(
                user_without_password.domain_name,
                user_without_password.email,
                _password_info(_PASSWORD),
            )
