"""Tests for the hash cost of ``AuthDBSource.verify_credential`` refusals against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from unittest.mock import patch

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.auth import AuthorizationFailed, PasswordMismatch
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.hasher.pbkdf2 import PBKDF2_SHA256Hasher
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.auth.db_source.db_source import AuthDBSource
from ai.backend.testutils.db import with_tables

_PASSWORD = "test_password"


def _password_info(password: str) -> PasswordInfo:
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


@dataclass(frozen=True)
class _Domain:
    name: str


@dataclass(frozen=True)
class _Credential:
    domain_name: str
    email: str
    user_uuid: uuid.UUID


class TestVerifyCredentialRejection:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                LoginClientTypeRow,
                LoginSessionRow,
                LoginHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def auth_db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> AuthDBSource:
        return AuthDBSource(db_with_cleanup)

    @pytest.fixture
    async def domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> _Domain:
        domain = _Domain(name=f"domain-{uuid.uuid4().hex[:8]}")
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain.name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
        return domain

    @pytest.fixture
    async def user_resource_policy_name(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
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
        return name

    async def _add_user(
        self,
        db: ExtendedAsyncSAEngine,
        domain: _Domain,
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
                    domain_name=domain.name,
                    role=UserRole.USER,
                    resource_policy=resource_policy,
                )
            )
        return _Credential(domain_name=domain.name, email=email, user_uuid=user_uuid)

    @pytest.fixture
    async def user_with_password(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain: _Domain,
        user_resource_policy_name: str,
    ) -> _Credential:
        return await self._add_user(
            db_with_cleanup, domain, user_resource_policy_name, _password_info(_PASSWORD)
        )

    @pytest.fixture
    async def user_without_password(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        domain: _Domain,
        user_resource_policy_name: str,
    ) -> _Credential:
        return await self._add_user(db_with_cleanup, domain, user_resource_policy_name, None)

    async def test_returns_the_user_for_a_matching_credential(
        self,
        auth_db_source: AuthDBSource,
        user_with_password: _Credential,
    ) -> None:
        result = await auth_db_source.verify_credential(
            user_with_password.domain_name, user_with_password.email, _password_info(_PASSWORD)
        )

        assert result.user.uuid == user_with_password.user_uuid

    async def test_a_wrong_password_names_the_user(
        self,
        auth_db_source: AuthDBSource,
        user_with_password: _Credential,
    ) -> None:
        with pytest.raises(PasswordMismatch) as raised:
            await auth_db_source.verify_credential(
                user_with_password.domain_name,
                user_with_password.email,
                _password_info("wrong_password"),
            )

        assert raised.value.user_id == user_with_password.user_uuid

    async def test_a_wrong_password_on_a_cheaper_stored_hash_costs_one_more_hash(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        auth_db_source: AuthDBSource,
        domain: _Domain,
        user_resource_policy_name: str,
    ) -> None:
        cheap_hash = PasswordInfo(
            password=_PASSWORD, algorithm=PasswordHashAlgorithm.SHA256, rounds=1, salt_size=32
        )
        user = await self._add_user(db_with_cleanup, domain, user_resource_policy_name, cheap_hash)

        with (
            patch.object(
                PBKDF2_SHA256Hasher,
                "generate_new_hash",
                autospec=True,
                side_effect=PBKDF2_SHA256Hasher.generate_new_hash,
            ) as hashed,
            pytest.raises(PasswordMismatch),
        ):
            await auth_db_source.verify_credential(
                user.domain_name, user.email, _password_info("wrong_password")
            )

        hashed.assert_called_once()

    async def test_a_wrong_password_on_a_configured_hash_costs_no_extra_hash(
        self,
        auth_db_source: AuthDBSource,
        user_with_password: _Credential,
    ) -> None:
        with (
            patch.object(
                PBKDF2_SHA256Hasher,
                "generate_new_hash",
                autospec=True,
                side_effect=PBKDF2_SHA256Hasher.generate_new_hash,
            ) as hashed,
            pytest.raises(PasswordMismatch),
        ):
            await auth_db_source.verify_credential(
                user_with_password.domain_name,
                user_with_password.email,
                _password_info("wrong_password"),
            )

        hashed.assert_not_called()

    async def test_a_wrong_password_on_a_costlier_stored_hash_costs_no_extra_hash(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        auth_db_source: AuthDBSource,
        domain: _Domain,
        user_resource_policy_name: str,
    ) -> None:
        configured = _password_info(_PASSWORD)
        costlier_hash = PasswordInfo(
            password=_PASSWORD,
            algorithm=configured.algorithm,
            rounds=configured.rounds + 1,
            salt_size=32,
        )
        user = await self._add_user(
            db_with_cleanup, domain, user_resource_policy_name, costlier_hash
        )

        with (
            patch.object(
                PBKDF2_SHA256Hasher,
                "generate_new_hash",
                autospec=True,
                side_effect=PBKDF2_SHA256Hasher.generate_new_hash,
            ) as hashed,
            pytest.raises(PasswordMismatch),
        ):
            await auth_db_source.verify_credential(
                user.domain_name, user.email, _password_info("wrong_password")
            )

        hashed.assert_not_called()

    async def test_a_wrong_password_on_a_hash_of_another_algorithm_costs_no_extra_hash(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        auth_db_source: AuthDBSource,
        domain: _Domain,
        user_resource_policy_name: str,
    ) -> None:
        # bcrypt and PBKDF2 rounds do not compare, so nothing is topped up.
        bcrypt_hash = PasswordInfo(
            password=_PASSWORD, algorithm=PasswordHashAlgorithm.BCRYPT, rounds=4, salt_size=32
        )
        user = await self._add_user(db_with_cleanup, domain, user_resource_policy_name, bcrypt_hash)

        with (
            patch.object(
                PBKDF2_SHA256Hasher,
                "generate_new_hash",
                autospec=True,
                side_effect=PBKDF2_SHA256Hasher.generate_new_hash,
            ) as hashed,
            pytest.raises(PasswordMismatch),
        ):
            await auth_db_source.verify_credential(
                user.domain_name, user.email, _password_info("wrong_password")
            )

        hashed.assert_not_called()

    async def test_an_unknown_email_is_refused_after_one_hash(
        self,
        auth_db_source: AuthDBSource,
        user_with_password: _Credential,
    ) -> None:
        with (
            patch.object(
                PBKDF2_SHA256Hasher,
                "generate_new_hash",
                autospec=True,
                side_effect=PBKDF2_SHA256Hasher.generate_new_hash,
            ) as hashed,
            pytest.raises(AuthorizationFailed) as raised,
        ):
            await auth_db_source.verify_credential(
                user_with_password.domain_name, "nobody@example.com", _password_info(_PASSWORD)
            )

        assert not isinstance(raised.value, PasswordMismatch)
        hashed.assert_called_once()

    async def test_a_user_without_a_password_is_refused_after_one_hash(
        self,
        auth_db_source: AuthDBSource,
        user_without_password: _Credential,
    ) -> None:
        with (
            patch.object(
                PBKDF2_SHA256Hasher,
                "generate_new_hash",
                autospec=True,
                side_effect=PBKDF2_SHA256Hasher.generate_new_hash,
            ) as hashed,
            pytest.raises(AuthorizationFailed) as raised,
        ):
            await auth_db_source.verify_credential(
                user_without_password.domain_name,
                user_without_password.email,
                _password_info(_PASSWORD),
            )

        assert not isinstance(raised.value, PasswordMismatch)
        hashed.assert_called_once()
