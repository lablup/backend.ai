"""The HuggingFace registry DataLoader path: each registry is answered for."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.v2.huggingface_registry.response import HuggingFaceRegistryNode
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.huggingface_registry.adapter import HuggingFaceRegistryAdapter
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.data.huggingface_registry.types import (
    HuggingFaceRegistryConnectionData,
    HuggingFaceRegistryData,
)
from ai.backend.manager.defs import TOKEN_PLACEHOLDER
from ai.backend.manager.errors.common import GenericForbidden

READABLE = ArtifactRegistryID(uuid4())
DENIED = ArtifactRegistryID(uuid4())
ABSENT = ArtifactRegistryID(uuid4())
_TOKEN = "stored-token"
_URL = "https://huggingface.test.local"


@dataclass(frozen=True)
class _TokenCase:
    role: UserRole
    expected_token: str


def _user_with_role(role: UserRole) -> UserData:
    return UserData(
        user_id=uuid4(),
        is_authorized=True,
        is_admin=role in (UserRole.SUPERADMIN, UserRole.ADMIN),
        is_superadmin=role == UserRole.SUPERADMIN,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid4()),
    )


@pytest.fixture
def connection() -> HuggingFaceRegistryConnectionData:
    return HuggingFaceRegistryConnectionData(
        id=READABLE, url="https://huggingface.test.local", token=None
    )


@pytest.fixture
def meta() -> ArtifactRegistryData:
    return ArtifactRegistryData(
        id=ArtifactRegistryID(uuid4()),
        registry_id=READABLE,
        name="huggingface",
        type=ArtifactRegistryType.HUGGINGFACE,
    )


@pytest.fixture
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this registry")


@pytest.fixture
def processors(
    connection: HuggingFaceRegistryConnectionData,
    meta: ArtifactRegistryData,
    denial: GenericForbidden,
) -> MagicMock:
    processors = MagicMock()
    processors.bulk_get_huggingface_registries.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[HuggingFaceRegistryConnectionData].succeeded(
                    READABLE, connection
                ),
                PartialBulkEntityResult[HuggingFaceRegistryConnectionData].denied(DENIED, denial),
                PartialBulkEntityResult[HuggingFaceRegistryConnectionData].nothing(ABSENT),
            ]
        )
    )
    processors.get_registry_metas.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[PartialBulkEntityResult[ArtifactRegistryData].succeeded(READABLE, meta)]
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> HuggingFaceRegistryAdapter:
    return HuggingFaceRegistryAdapter(processors)


async def test_batch_load_answers_per_id(
    adapter: HuggingFaceRegistryAdapter,
    denial: GenericForbidden,
) -> None:
    node, refused, missing = await adapter.batch_load_by_ids([READABLE, DENIED, ABSENT])

    assert node is not None and not isinstance(node, Exception)
    assert node.id == READABLE
    assert node.name == "huggingface"
    assert refused is denial
    assert missing is None


async def test_no_ids_read_nothing(
    adapter: HuggingFaceRegistryAdapter, processors: MagicMock
) -> None:
    assert await adapter.batch_load_by_ids([]) == []
    processors.bulk_get_huggingface_registries.run.assert_not_awaited()
    processors.get_registry_metas.run.assert_not_awaited()


@pytest.fixture
def adapter_of_a_registry_with_a_token(meta: ArtifactRegistryData) -> HuggingFaceRegistryAdapter:
    processors = MagicMock()
    processors.get_huggingface_registry.run = AsyncMock(
        return_value=MagicMock(
            result=HuggingFaceRegistryData(id=READABLE, name="huggingface", url=_URL, token=_TOKEN)
        )
    )
    processors.bulk_get_huggingface_registries.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[HuggingFaceRegistryConnectionData].succeeded(
                    READABLE,
                    HuggingFaceRegistryConnectionData(id=READABLE, url=_URL, token=_TOKEN),
                ),
            ]
        )
    )
    processors.get_registry_metas.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[PartialBulkEntityResult[ArtifactRegistryData].succeeded(READABLE, meta)]
        )
    )
    return HuggingFaceRegistryAdapter(processors)


@pytest.mark.parametrize(
    "case",
    [
        _TokenCase(role=UserRole.SUPERADMIN, expected_token=_TOKEN),
        _TokenCase(role=UserRole.MONITOR, expected_token=TOKEN_PLACEHOLDER),
        _TokenCase(role=UserRole.ADMIN, expected_token=TOKEN_PLACEHOLDER),
        _TokenCase(role=UserRole.USER, expected_token=TOKEN_PLACEHOLDER),
    ],
    ids=lambda case: case.role.value,
)
async def test_get_gives_the_token_only_to_a_superadmin(
    adapter_of_a_registry_with_a_token: HuggingFaceRegistryAdapter,
    case: _TokenCase,
) -> None:
    with with_user_context(_user_with_role(case.role)):
        node = await adapter_of_a_registry_with_a_token.get(READABLE)

    assert node.token == case.expected_token


@pytest.mark.parametrize(
    "case",
    [
        _TokenCase(role=UserRole.SUPERADMIN, expected_token=_TOKEN),
        _TokenCase(role=UserRole.MONITOR, expected_token=TOKEN_PLACEHOLDER),
        _TokenCase(role=UserRole.ADMIN, expected_token=TOKEN_PLACEHOLDER),
        _TokenCase(role=UserRole.USER, expected_token=TOKEN_PLACEHOLDER),
    ],
    ids=lambda case: case.role.value,
)
async def test_batch_load_gives_the_token_only_to_a_superadmin(
    adapter_of_a_registry_with_a_token: HuggingFaceRegistryAdapter,
    case: _TokenCase,
) -> None:
    with with_user_context(_user_with_role(case.role)):
        [node] = await adapter_of_a_registry_with_a_token.batch_load_by_ids([READABLE])

    assert isinstance(node, HuggingFaceRegistryNode)
    assert node.token == case.expected_token


async def test_a_registry_without_a_token_stays_null(
    adapter: HuggingFaceRegistryAdapter,
) -> None:
    with with_user_context(_user_with_role(UserRole.USER)):
        node, _, _ = await adapter.batch_load_by_ids([READABLE, DENIED, ABSENT])

    assert isinstance(node, HuggingFaceRegistryNode)
    assert node.token is None
