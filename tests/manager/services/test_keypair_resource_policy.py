from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

import pytest
import sqlalchemy as sa

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.errors.storage import ObjectNotFound
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.keypair_resource_policy.repository import (
    KeypairResourcePolicyRepository,
)
from ai.backend.manager.services.keypair_resource_policy.actions.create_keypair_resource_policy import (
    CreateKeyPairResourcePolicyAction,
    CreateKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.delete_keypair_resource_policy import (
    DeleteKeyPairResourcePolicyAction,
    DeleteKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.actions.modify_keypair_resource_policy import (
    KeyPairResourcePolicyModifier,
    ModifyKeyPairResourcePolicyAction,
    ModifyKeyPairResourcePolicyActionResult,
)
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.keypair_resource_policy.service import KeypairResourcePolicyService
from ai.backend.manager.services.keypair_resource_policy.types import KeyPairResourcePolicyCreator
from ai.backend.manager.types import OptionalState, TriState

from .utils import ScenarioBase


@pytest.fixture
def keypair_resource_policy_repository(database_engine: ExtendedAsyncSAEngine):
    return KeypairResourcePolicyRepository(db=database_engine)


@pytest.fixture
def keypair_resource_policy_service(
    keypair_resource_policy_repository: KeypairResourcePolicyRepository,
):
    return KeypairResourcePolicyService(
        keypair_resource_policy_repository=keypair_resource_policy_repository
    )


@pytest.fixture
def processors(keypair_resource_policy_service) -> KeypairResourcePolicyProcessors:
    return KeypairResourcePolicyProcessors(keypair_resource_policy_service, [])


@pytest.fixture
def create_keypair_resource_policy(database_engine: ExtendedAsyncSAEngine):
    @asynccontextmanager
    async def _create_keypair_resource_policy(
        name: str,
        *,
        default_for_unspecified: DefaultForUnspecified = DefaultForUnspecified.LIMITED,
        total_resource_slots: Optional[ResourceSlot] = None,
        max_session_lifetime: int = 0,
        max_concurrent_sessions: int = 30,
        max_pending_session_count: Optional[int] = None,
        max_pending_session_resource_slots: Optional[ResourceSlot] = None,
        max_concurrent_sftp_sessions: int = 10,
        max_containers_per_session: int = 1,
        idle_timeout: int = 1800,
        allowed_vfolder_hosts: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[KeyPairResourcePolicyData, None]:
        if total_resource_slots is None:
            total_resource_slots = ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None)
        if allowed_vfolder_hosts is None:
            allowed_vfolder_hosts = {}

        policy_data = {
            "name": name,
            "created_at": datetime.now(),
            "default_for_unspecified": default_for_unspecified,
            "total_resource_slots": total_resource_slots,
            "max_session_lifetime": max_session_lifetime,
            "max_concurrent_sessions": max_concurrent_sessions,
            "max_pending_session_count": max_pending_session_count,
            "max_pending_session_resource_slots": max_pending_session_resource_slots,
            "max_concurrent_sftp_sessions": max_concurrent_sftp_sessions,
            "max_containers_per_session": max_containers_per_session,
            "idle_timeout": idle_timeout,
            "allowed_vfolder_hosts": allowed_vfolder_hosts,
        }

        async with database_engine.begin_session() as session:
            db_row = KeyPairResourcePolicyRow(**policy_data)
            session.add(db_row)
            await session.commit()
            result = db_row.to_dataclass()

        try:
            yield result
        finally:
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(KeyPairResourcePolicyRow).where(KeyPairResourcePolicyRow.name == name)
                )

    return _create_keypair_resource_policy


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Create keypair resource policy with valid data",
            CreateKeyPairResourcePolicyAction(
                creator=KeyPairResourcePolicyCreator(
                    name="test-create-policy",
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "2", "mem": "4g"}, None
                    ),
                    max_session_lifetime=1800,
                    max_concurrent_sessions=3,
                    max_pending_session_count=5,
                    max_pending_session_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "1", "mem": "2g"}, None
                    ),
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=1,
                    idle_timeout=900,
                    allowed_vfolder_hosts={"local": {}},
                    max_vfolder_count=3,  # Deprecated but still in creator
                    max_vfolder_size=500,  # Deprecated but still in creator
                    max_quota_scope_size=250,  # Deprecated but still in creator
                )
            ),
            CreateKeyPairResourcePolicyActionResult(
                keypair_resource_policy=KeyPairResourcePolicyData(
                    name="test-create-policy",
                    created_at=datetime.now(),
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "2", "mem": "4g"}, None
                    ),
                    max_session_lifetime=1800,
                    max_concurrent_sessions=3,
                    max_pending_session_count=5,
                    max_pending_session_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "1", "mem": "2g"}, None
                    ),
                    max_concurrent_sftp_sessions=2,
                    max_containers_per_session=1,
                    idle_timeout=900,
                    allowed_vfolder_hosts={"local": set()},
                )
            ),
        ),
        ScenarioBase.success(
            "Create keypair resource policy with minimal configuration",
            CreateKeyPairResourcePolicyAction(
                creator=KeyPairResourcePolicyCreator(
                    name="minimal-policy",
                    allowed_vfolder_hosts={},
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    idle_timeout=1800,
                    max_concurrent_sessions=1,
                    max_containers_per_session=1,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_quota_scope_size=None,
                    max_vfolder_count=None,
                    max_vfolder_size=None,
                    max_concurrent_sftp_sessions=1,
                    max_session_lifetime=0,
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "1", "mem": "1g"}, None
                    ),
                )
            ),
            CreateKeyPairResourcePolicyActionResult(
                keypair_resource_policy=KeyPairResourcePolicyData(
                    name="minimal-policy",
                    created_at=datetime.now(),
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "1", "mem": "1g"}, None
                    ),
                    max_session_lifetime=0,
                    max_concurrent_sessions=1,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_concurrent_sftp_sessions=1,
                    max_containers_per_session=1,
                    idle_timeout=1800,
                    allowed_vfolder_hosts={},
                )
            ),
        ),
    ],
)
async def test_create_keypair_resource_policy(
    test_scenario: ScenarioBase,
    processors: KeypairResourcePolicyProcessors,
) -> None:
    await test_scenario.test(processors.create_keypair_resource_policy.wait_for_complete)


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.failure(
            "Create keypair resource policy with duplicate name should raise error",
            CreateKeyPairResourcePolicyAction(
                creator=KeyPairResourcePolicyCreator(
                    name="existing-policy",
                    allowed_vfolder_hosts=None,
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    idle_timeout=None,
                    max_concurrent_sessions=None,
                    max_containers_per_session=None,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_quota_scope_size=None,
                    max_vfolder_count=None,
                    max_vfolder_size=None,
                    max_concurrent_sftp_sessions=None,
                    max_session_lifetime=None,
                    total_resource_slots=None,
                )
            ),
            Exception,  # Database constraint violation
        ),
    ],
)
async def test_create_keypair_resource_policy_failure(
    test_scenario: ScenarioBase,
    processors: KeypairResourcePolicyProcessors,
) -> None:
    await test_scenario.test(processors.create_keypair_resource_policy.wait_for_complete)


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Modify keypair resource policy with valid data",
            ModifyKeyPairResourcePolicyAction(
                name="test-modify-policy",
                modifier=KeyPairResourcePolicyModifier(
                    max_concurrent_sessions=OptionalState.update(10),
                    idle_timeout=OptionalState.update(3600),
                    max_containers_per_session=OptionalState.update(3),
                    max_pending_session_count=TriState.update(20),
                    allowed_vfolder_hosts=OptionalState.update({"shared": {}}),
                ),
            ),
            ModifyKeyPairResourcePolicyActionResult(
                keypair_resource_policy=KeyPairResourcePolicyData(
                    name="test-modify-policy",
                    created_at=datetime.now(),
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "4", "mem": "8g"}, None
                    ),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_pending_session_count=20,
                    max_pending_session_resource_slots=None,
                    max_concurrent_sftp_sessions=10,
                    max_containers_per_session=3,
                    idle_timeout=3600,
                    allowed_vfolder_hosts={"shared": {}},
                )
            ),
        ),
        ScenarioBase.success(
            "Modify keypair resource policy with tristate nullify",
            ModifyKeyPairResourcePolicyAction(
                name="test-nullify-policy",
                modifier=KeyPairResourcePolicyModifier(
                    max_pending_session_count=TriState.nullify(),
                    max_pending_session_resource_slots=TriState.nullify(),
                ),
            ),
            ModifyKeyPairResourcePolicyActionResult(
                keypair_resource_policy=KeyPairResourcePolicyData(
                    name="test-nullify-policy",
                    created_at=datetime.now(),
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "4", "mem": "8g"}, None
                    ),
                    max_session_lifetime=0,
                    max_concurrent_sessions=30,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_concurrent_sftp_sessions=10,
                    max_containers_per_session=1,
                    idle_timeout=1800,
                    allowed_vfolder_hosts={},
                )
            ),
        ),
        ScenarioBase.success(
            "Modify keypair resource policy with complete resource slots replacement",
            ModifyKeyPairResourcePolicyAction(
                name="test-resource-replacement-policy",
                modifier=KeyPairResourcePolicyModifier(
                    total_resource_slots=OptionalState.update(
                        ResourceSlot.from_user_input(
                            {"cpu": "100", "mem": "512g", "gpu": "8"}, None
                        )
                    ),
                ),
            ),
            ModifyKeyPairResourcePolicyActionResult(
                keypair_resource_policy=KeyPairResourcePolicyData(
                    name="test-resource-replacement-policy",
                    created_at=datetime.now(),
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "100", "mem": "512g", "gpu": "8"}, None
                    ),
                    max_session_lifetime=0,
                    max_concurrent_sessions=30,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_concurrent_sftp_sessions=10,
                    max_containers_per_session=1,
                    idle_timeout=1800,
                    allowed_vfolder_hosts={},
                )
            ),
        ),
    ],
)
async def test_modify_keypair_resource_policy(
    test_scenario: ScenarioBase,
    processors: KeypairResourcePolicyProcessors,
    create_keypair_resource_policy,
) -> None:
    async def test_function(action: ModifyKeyPairResourcePolicyAction):
        async with create_keypair_resource_policy(name=action.name) as _:
            return await processors.modify_keypair_resource_policy.wait_for_complete(action)

    await test_scenario.test(test_function)


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.failure(
            "Modify non-existent keypair resource policy should raise ObjectNotFound",
            ModifyKeyPairResourcePolicyAction(
                name="non-existent-policy",
                modifier=KeyPairResourcePolicyModifier(
                    max_concurrent_sessions=OptionalState.update(5),
                ),
            ),
            ObjectNotFound,
        ),
    ],
)
async def test_modify_keypair_resource_policy_failure(
    test_scenario: ScenarioBase,
    processors: KeypairResourcePolicyProcessors,
) -> None:
    await test_scenario.test(processors.modify_keypair_resource_policy.wait_for_complete)


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Delete existing keypair resource policy",
            DeleteKeyPairResourcePolicyAction(name="test-delete-policy"),
            DeleteKeyPairResourcePolicyActionResult(
                keypair_resource_policy=KeyPairResourcePolicyData(
                    name="test-delete-policy",
                    created_at=datetime.now(),
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot.from_user_input(
                        {"cpu": "4", "mem": "8g"}, None
                    ),
                    max_session_lifetime=0,
                    max_concurrent_sessions=30,
                    max_pending_session_count=None,
                    max_pending_session_resource_slots=None,
                    max_concurrent_sftp_sessions=10,
                    max_containers_per_session=1,
                    idle_timeout=1800,
                    allowed_vfolder_hosts={},
                )
            ),
        ),
    ],
)
async def test_delete_keypair_resource_policy(
    test_scenario: ScenarioBase,
    processors: KeypairResourcePolicyProcessors,
    create_keypair_resource_policy,
    database_engine: ExtendedAsyncSAEngine,
) -> None:
    async def test_function(action: DeleteKeyPairResourcePolicyAction):
        async with create_keypair_resource_policy(name=action.name) as _:
            result = await processors.delete_keypair_resource_policy.wait_for_complete(action)

            # Verify the policy was deleted from the database
            async with database_engine.begin_session() as session:
                db_row = await session.scalar(
                    sa.select(KeyPairResourcePolicyRow).where(
                        KeyPairResourcePolicyRow.name == action.name
                    )
                )
                assert db_row is None

            return result

    await test_scenario.test(test_function)


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.failure(
            "Delete non-existent keypair resource policy should raise ObjectNotFound",
            DeleteKeyPairResourcePolicyAction(name="non-existent-policy"),
            ObjectNotFound,
        ),
    ],
)
async def test_delete_keypair_resource_policy_failure(
    test_scenario: ScenarioBase,
    processors: KeypairResourcePolicyProcessors,
) -> None:
    await test_scenario.test(processors.delete_keypair_resource_policy.wait_for_complete)
