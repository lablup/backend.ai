"""Object storage nodes carry the secret key only for a superadmin."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.v2.object_storage.request import (
    AdminSearchObjectStoragesInput,
)
from ai.backend.common.dto.manager.v2.object_storage.response import ObjectStorageNode
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, EntityOpsResult
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.defs import SECRET_KEY_PLACEHOLDER

_SECRET_KEY = "real-secret"


@pytest.fixture
def storage() -> ObjectStorageData:
    return ObjectStorageData(
        id=ObjectStorageID(uuid4()),
        name="minio",
        host="minio.local",
        access_key="access",
        secret_key=_SECRET_KEY,
        endpoint="http://minio.local:9000",
        region=None,
    )


@pytest.fixture
def adapter(storage: ObjectStorageData) -> ObjectStorageAdapter:
    processors = MagicMock()
    processors.get.run = AsyncMock(return_value=EntityOpsResult(data=storage))
    processors.global_search_object_storages.run = AsyncMock(
        return_value=BatchOpsResult(
            items=[storage], total_count=1, has_next_page=False, has_previous_page=False
        )
    )
    processors.bulk_get.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[PartialBulkEntityResult[ObjectStorageData].succeeded(storage.id, storage)]
        )
    )
    return ObjectStorageAdapter(processors)


@pytest.fixture(
    params=[UserRole.SUPERADMIN, UserRole.MONITOR, UserRole.ADMIN, UserRole.USER],
    ids=["superadmin", "monitor", "domain_admin", "user"],
)
def caller_role(request: pytest.FixtureRequest) -> Iterator[UserRole]:
    role: UserRole = request.param
    user = UserData(
        user_id=uuid4(),
        is_authorized=True,
        is_admin=role in (UserRole.SUPERADMIN, UserRole.ADMIN),
        is_superadmin=role == UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid4()),
    )
    with with_user(user):
        yield role


def _expected_secret(role: UserRole) -> str:
    return _SECRET_KEY if role == UserRole.SUPERADMIN else SECRET_KEY_PLACEHOLDER


class TestObjectStorageSecretKey:
    async def test_get_reveals_the_secret_only_to_a_superadmin(
        self, adapter: ObjectStorageAdapter, storage: ObjectStorageData, caller_role: UserRole
    ) -> None:
        node = await adapter.get(storage.id)

        assert node.secret_key == _expected_secret(caller_role)

    async def test_search_reveals_the_secret_only_to_a_superadmin(
        self, adapter: ObjectStorageAdapter, caller_role: UserRole
    ) -> None:
        payload = await adapter.admin_search(AdminSearchObjectStoragesInput())

        assert [item.secret_key for item in payload.items] == [_expected_secret(caller_role)]

    async def test_the_dataloader_reveals_the_secret_only_to_a_superadmin(
        self, adapter: ObjectStorageAdapter, storage: ObjectStorageData, caller_role: UserRole
    ) -> None:
        nodes = await adapter.batch_load_by_ids([storage.id])

        assert [node.secret_key for node in nodes if isinstance(node, ObjectStorageNode)] == [
            _expected_secret(caller_role)
        ]
