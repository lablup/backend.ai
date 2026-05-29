"""DB-level tests for the keypair nested filter on keypair resource policies (BA-6243).

These verify that ``KeypairResourcePolicyConditions.exists_keypair_combined`` composed
with ``KeypairConditions.by_user_id_equals`` — exactly what the adapter builds for
``KeypairResourcePolicyFilter.keypair`` — discriminates between policies via the
``keypairs.resource_policy = keypair_resource_policies.name`` correlation. SQL-string
unit tests cannot catch a broken correlation; these can.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.keypair.conditions import KeypairConditions
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_policy.conditions import KeypairResourcePolicyConditions
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.testutils.db import with_tables

_DOMAIN = "test-domain"
_P1 = "krp-policy-1"
_P2 = "krp-policy-2"
# user A owns keypairs on BOTH policies; user B owns a keypair on P2 only.
_USER_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
_USER_B = uuid.UUID("22222222-2222-2222-2222-222222222222")
_UNKNOWN = uuid.UUID("99999999-9999-9999-9999-999999999999")


def _user_exists_condition(user_id: uuid.UUID) -> sa.sql.expression.ColumnElement[bool]:
    """Reproduce what the adapter builds for filter.keypair.userId == user_id."""
    inner = KeypairConditions.by_user_id_equals(UUIDEqualMatchSpec(value=user_id, negated=False))
    return KeypairResourcePolicyConditions.exists_keypair_combined([inner])()


class TestKeypairNestedFilterDiscrimination:
    @pytest.fixture
    async def seeded_db(
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
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            async with database_connection.begin_session() as db_sess:
                db_sess.add(
                    DomainRow(
                        name=_DOMAIN,
                        description="d",
                        is_active=True,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts={},
                        allowed_docker_registries=[],
                    )
                )
                db_sess.add(
                    UserResourcePolicyRow(
                        name="default",
                        max_vfolder_count=10,
                        max_quota_scope_size=-1,
                        max_session_count_per_model_session=5,
                        max_customized_image_count=3,
                    )
                )
                for pname in (_P1, _P2):
                    db_sess.add(
                        KeyPairResourcePolicyRow(
                            name=pname,
                            total_resource_slots=ResourceSlot(),
                            max_session_lifetime=0,
                            max_concurrent_sessions=10,
                            max_concurrent_sftp_sessions=1,
                            max_containers_per_session=1,
                            idle_timeout=0,
                        )
                    )
                await db_sess.flush()

                for uid, email in ((_USER_A, "a@example.com"), (_USER_B, "b@example.com")):
                    db_sess.add(
                        UserRow(
                            uuid=uid,
                            username=email.split("@")[0],
                            email=email,
                            password=None,
                            need_password_change=False,
                            status=UserStatus.ACTIVE,
                            status_info="active",
                            domain_name=_DOMAIN,
                            role=UserRole.USER,
                            resource_policy="default",
                        )
                    )
                await db_sess.flush()

                # user A: keypair on P1 AND on P2; user B: keypair on P2 only.
                keypairs = [
                    ("a@example.com", _USER_A, "AKA0000000000000P1AA", _P1),
                    ("a@example.com", _USER_A, "AKA0000000000000P2AA", _P2),
                    ("b@example.com", _USER_B, "AKB0000000000000P2BB", _P2),
                ]
                for email, uid, ak, rp in keypairs:
                    db_sess.add(
                        KeyPairRow(
                            user_id=email,
                            user=uid,
                            access_key=ak,
                            secret_key="s",
                            is_active=True,
                            is_admin=False,
                            resource_policy=rp,
                            rate_limit=1000,
                        )
                    )
            yield database_connection

    async def _policies_for(self, db: ExtendedAsyncSAEngine, user_id: uuid.UUID) -> set[str]:
        async with db.begin_readonly_session() as sess:
            result = await sess.execute(
                sa.select(KeyPairResourcePolicyRow.name).where(_user_exists_condition(user_id))
            )
            return {row[0] for row in result}

    async def test_user_with_keypairs_on_both_policies(
        self, seeded_db: ExtendedAsyncSAEngine
    ) -> None:
        assert await self._policies_for(seeded_db, _USER_A) == {_P1, _P2}

    async def test_user_excluded_from_policy_without_their_keypair(
        self, seeded_db: ExtendedAsyncSAEngine
    ) -> None:
        # user B owns a keypair only on P2 — the correlation must exclude P1.
        assert await self._policies_for(seeded_db, _USER_B) == {_P2}

    async def test_unknown_user_matches_no_policy(self, seeded_db: ExtendedAsyncSAEngine) -> None:
        assert await self._policies_for(seeded_db, _UNKNOWN) == set()
