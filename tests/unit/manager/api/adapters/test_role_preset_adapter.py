"""The role preset node names the global entity a global preset is created in and carries
the role name template."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.manager.api.adapters.role_preset.adapter import RolePresetAdapter
from ai.backend.manager.data.permission.global_entity import GlobalEntityIDCache
from ai.backend.manager.data.role_preset.types import RolePresetData

_GLOBAL_ID = GlobalEntityID(UUID("00000000-0000-0000-0000-000000000001"))
_PUBLIC_ID = GlobalEntityID(UUID("00000000-0000-0000-0000-000000000002"))
_DOMAIN_ID = UUID("00000000-0000-0000-0000-000000000003")
_PRESET_ID = RolePresetID(uuid4())


@dataclass(frozen=True)
class _ScopeCase:
    scope_type: EntityType
    scope_id: UUID | None
    expected: GlobalEntityName | None


@pytest.fixture(autouse=True)
def loaded_ids() -> Iterator[None]:
    GlobalEntityIDCache.fill({
        GlobalEntityName.GLOBAL: _GLOBAL_ID,
        GlobalEntityName.PUBLIC: _PUBLIC_ID,
    })
    yield
    GlobalEntityIDCache.clear()


@pytest.fixture
def preset(case: _ScopeCase) -> RolePresetData:
    return RolePresetData(
        id=_PRESET_ID,
        name="member",
        role_name_template="{{ scope.name }}-member",
        scope_type=case.scope_type,
        scope_id=case.scope_id,
        auto_assign=False,
        deleted=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def adapter(preset: RolePresetData) -> RolePresetAdapter:
    processors = MagicMock()
    processors.get.run = AsyncMock(return_value=MagicMock(data=preset))
    return RolePresetAdapter(processors)


class TestRolePresetNode:
    @pytest.mark.parametrize(
        "case",
        [
            _ScopeCase(
                scope_type=GlobalEntityType(),
                scope_id=_GLOBAL_ID,
                expected=GlobalEntityName.GLOBAL,
            ),
            _ScopeCase(
                scope_type=GlobalEntityType(),
                scope_id=_PUBLIC_ID,
                expected=GlobalEntityName.PUBLIC,
            ),
            _ScopeCase(scope_type=GlobalEntityType(), scope_id=None, expected=None),
            _ScopeCase(scope_type=DomainEntityType(), scope_id=_DOMAIN_ID, expected=None),
            _ScopeCase(scope_type=DomainEntityType(), scope_id=None, expected=None),
        ],
        ids=lambda case: f"{case.scope_type}-{case.scope_id}",
    )
    async def test_names_the_global_scope_and_carries_the_template(
        self, adapter: RolePresetAdapter, preset: RolePresetData, case: _ScopeCase
    ) -> None:
        node = await adapter.get(_PRESET_ID)

        assert node.scope == case.expected
        assert node.role_name_template == preset.role_name_template
