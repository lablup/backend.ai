"""Legacy GQL ``KeyPair.secret_key`` answers only to the keypair owner and superadmins."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import graphene
import pytest

from ai.backend.manager.api.gql_legacy.keypair import KeyPair
from ai.backend.manager.models.user.row import UserRole

_OWNER_ID = uuid.uuid4()
_STORED_SECRET = "encrypted-secret"
_PLAIN_SECRET = "plain-secret"


type MakeInfo = Callable[[UserRole, uuid.UUID], graphene.ResolveInfo]


@pytest.fixture
def make_info() -> MakeInfo:
    def _make(role: UserRole, user_id: uuid.UUID) -> graphene.ResolveInfo:
        ctx = MagicMock()
        ctx.user = {"role": role, "domain_name": "default", "uuid": user_id}
        ctx.key_provider_pool.decrypt = AsyncMock(return_value=_PLAIN_SECRET)
        info = MagicMock(spec=graphene.ResolveInfo)
        info.context = ctx
        return info

    return _make


@pytest.fixture
def keypair() -> KeyPair:
    return KeyPair(access_key="AKOWNER", secret_key=_STORED_SECRET, user=_OWNER_ID)


class TestKeyPairSecretKey:
    @pytest.mark.parametrize(
        "role",
        [UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN],
        ids=["user", "domain_admin", "superadmin"],
    )
    async def test_the_owner_reads_their_secret(
        self, keypair: KeyPair, make_info: MakeInfo, role: UserRole
    ) -> None:
        assert await keypair.resolve_secret_key(make_info(role, _OWNER_ID)) == _PLAIN_SECRET

    async def test_a_superadmin_reads_another_users_secret(
        self, keypair: KeyPair, make_info: MakeInfo
    ) -> None:
        info = make_info(UserRole.SUPERADMIN, uuid.uuid4())

        assert await keypair.resolve_secret_key(info) == _PLAIN_SECRET

    @pytest.mark.parametrize(
        "role",
        [UserRole.ADMIN, UserRole.MONITOR, UserRole.USER],
        ids=["domain_admin", "monitor", "user"],
    )
    async def test_others_get_no_secret(
        self, keypair: KeyPair, make_info: MakeInfo, role: UserRole
    ) -> None:
        assert await keypair.resolve_secret_key(make_info(role, uuid.uuid4())) is None
