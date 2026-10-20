from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.jwt.config import JWTConfig
from ai.backend.common.jwt.signer import JWTSigner
from ai.backend.common.jwt.types import JWTUserContext
from ai.backend.common.jwt.validator import JWTValidator
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.manager.api.rest.middleware.auth import (
    _AuthContext,
    _authenticate_via_hmac,
    _authenticate_via_jwt,
    sign_request,
)
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import TableOrORM, with_tables

SECRET_KEY = "test-secret-key-at-least-32-bytes-long"
SIGN_METHOD = "HMAC-SHA256"
API_VERSION = "v8.20240915"

ALL_ROWS: list[TableOrORM] = [
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
    VirtualEntityRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
    ScopeBindingRow,
    EntityLabelRow,
    ContainerRegistryRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    ReplicaGroupRow,
    RoutingRow,
    ResourcePresetRow,
]


def _hmac_headers(access_key: str = "", signature: str = "") -> dict[str, str]:
    headers = {
        "Date": datetime.now(UTC).isoformat(),
        "X-BackendAI-Version": API_VERSION,
        "Content-Type": "application/json",
        "Host": "localhost:8081",
    }
    if access_key:
        headers["Authorization"] = (
            f"BackendAI signMethod={SIGN_METHOD},credential={access_key}:{signature}"
        )
    return headers


async def _make_signed_request(access_key: str) -> web.Request:
    unsigned = make_mocked_request("GET", "/v2/foo", headers=_hmac_headers())
    unsigned["date"] = datetime.now(UTC)
    unsigned["raw_date"] = unsigned.headers["Date"]
    signature = await sign_request(SIGN_METHOD, unsigned, SECRET_KEY)
    headers = _hmac_headers(access_key, signature)
    headers["Date"] = unsigned.headers["Date"]
    return make_mocked_request("GET", "/v2/foo", headers=headers)


class TestAuthenticateByUserStatus:
    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, ALL_ROWS):
            yield database_connection

    @pytest.fixture
    def key_provider_pool(self) -> KeyProviderPool:
        return KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN)

    @pytest.fixture
    def jwt_config(self) -> JWTConfig:
        return JWTConfig(algorithm="HS256", token_expiration_seconds=900)

    async def _create_user(self, db: ExtendedAsyncSAEngine, status: UserStatus) -> AccessKey:
        domain_name = f"domain-{uuid.uuid4().hex[:8]}"
        domain_id = DomainID(uuid.uuid4())
        user_policy = f"user-policy-{uuid.uuid4().hex[:8]}"
        kp_policy = f"kp-policy-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        access_key = AccessKey(f"AK{uuid.uuid4().hex[:16]}")
        async with db.begin_session() as sess:
            sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            sess.add(
                UserResourcePolicyRow(
                    name=user_policy,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                )
            )
            sess.add(
                KeyPairResourcePolicyRow(
                    name=kp_policy,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=10,
                    idle_timeout=3600,
                )
            )
            await sess.flush()
            sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"user-{uuid.uuid4().hex[:8]}",
                    email=f"user-{uuid.uuid4().hex[:8]}@test.io",
                    domain_name=domain_name,
                    domain_id=domain_id,
                    role=UserRole.USER,
                    status=status,
                    resource_policy=user_policy,
                )
            )
            await sess.flush()
            sess.add(
                KeyPairRow(
                    access_key=access_key,
                    secret_key=SecretValue(SECRET_KEY),
                    user=user_uuid,
                    is_active=True,
                    is_default=True,
                    resource_policy=kp_policy,
                )
            )
        return access_key

    async def _authenticate_hmac(
        self, db: ExtendedAsyncSAEngine, key_provider_pool: KeyProviderPool, access_key: AccessKey
    ) -> _AuthContext | None:
        request = await _make_signed_request(access_key)
        return await _authenticate_via_hmac(request, db, key_provider_pool, AsyncMock())

    async def _authenticate_jwt(
        self,
        db: ExtendedAsyncSAEngine,
        key_provider_pool: KeyProviderPool,
        jwt_config: JWTConfig,
        access_key: AccessKey,
    ) -> _AuthContext | None:
        token = JWTSigner(jwt_config).generate_token(
            JWTUserContext(access_key=access_key, role=UserRole.USER.value), SECRET_KEY
        )
        return await _authenticate_via_jwt(
            db, key_provider_pool, JWTValidator(jwt_config), AsyncMock(), token
        )

    @pytest.mark.parametrize("status", [UserStatus.INACTIVE, UserStatus.BEFORE_VERIFICATION])
    async def test_hmac_rejects_user(
        self, db: ExtendedAsyncSAEngine, key_provider_pool: KeyProviderPool, status: UserStatus
    ) -> None:
        access_key = await self._create_user(db, status)
        with pytest.raises(AuthorizationFailed):
            await self._authenticate_hmac(db, key_provider_pool, access_key)

    @pytest.mark.parametrize("status", [UserStatus.INACTIVE, UserStatus.BEFORE_VERIFICATION])
    async def test_jwt_rejects_user(
        self,
        db: ExtendedAsyncSAEngine,
        key_provider_pool: KeyProviderPool,
        jwt_config: JWTConfig,
        status: UserStatus,
    ) -> None:
        access_key = await self._create_user(db, status)
        with pytest.raises(AuthorizationFailed):
            await self._authenticate_jwt(db, key_provider_pool, jwt_config, access_key)

    async def test_hmac_accepts_active_user(
        self, db: ExtendedAsyncSAEngine, key_provider_pool: KeyProviderPool
    ) -> None:
        access_key = await self._create_user(db, UserStatus.ACTIVE)
        assert await self._authenticate_hmac(db, key_provider_pool, access_key) is not None

    async def test_jwt_accepts_active_user(
        self, db: ExtendedAsyncSAEngine, key_provider_pool: KeyProviderPool, jwt_config: JWTConfig
    ) -> None:
        access_key = await self._create_user(db, UserStatus.ACTIVE)
        assert (
            await self._authenticate_jwt(db, key_provider_pool, jwt_config, access_key) is not None
        )
