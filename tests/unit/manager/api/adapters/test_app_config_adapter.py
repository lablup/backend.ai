"""Unit tests for AppConfigAdapter DTO conversions and the resolve input contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config.request import ResolveAppConfigInput
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData


class TestAppConfigAdapterConverters:
    def test_fragment_to_node_maps_all_fields(self) -> None:
        created = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        updated = datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC)
        fragment_id = AppConfigFragmentID(uuid4())
        scope_id = AppConfigScopeID(uuid4())
        data = AppConfigFragmentData(
            id=fragment_id,
            config_name="theme",
            scope_type=AppConfigScopeType.DOMAIN,
            scope_id=scope_id,
            config={"color": "dark"},
            created_at=created,
            updated_at=updated,
        )

        node = AppConfigAdapter._fragment_to_node(data)

        assert node.id == fragment_id
        assert node.config_name == "theme"
        assert node.scope_type == AppConfigScopeType.DOMAIN
        assert node.scope_id == scope_id
        assert node.config == {"color": "dark"}
        assert node.created_at == created
        assert node.updated_at == updated

    @dataclass(frozen=True)
    class _ScopeCase:
        scope_type: AppConfigScopeType
        scope_id: AppConfigScopeID | None

    @pytest.mark.parametrize(
        "case",
        [
            _ScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id=None),
            _ScopeCase(scope_type=AppConfigScopeType.DOMAIN, scope_id=AppConfigScopeID(uuid4())),
            _ScopeCase(scope_type=AppConfigScopeType.USER, scope_id=AppConfigScopeID(uuid4())),
        ],
        ids=lambda case: case.scope_type.value,
    )
    def test_fragment_to_node_maps_every_scope_type(self, case: _ScopeCase) -> None:
        data = AppConfigFragmentData(
            id=AppConfigFragmentID(uuid4()),
            config_name="theme",
            scope_type=case.scope_type,
            scope_id=case.scope_id,
            config={},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        node = AppConfigAdapter._fragment_to_node(data)

        assert node.scope_type == case.scope_type
        assert node.scope_id == case.scope_id

    def test_app_config_to_node_maps_fields_and_preserves_fragment_order(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=UTC)
        first = AppConfigFragmentData(
            id=AppConfigFragmentID(uuid4()),
            config_name="theme",
            scope_type=AppConfigScopeType.PUBLIC,
            scope_id=None,
            config={"color": "light"},
            created_at=now,
            updated_at=now,
        )
        second = AppConfigFragmentData(
            id=AppConfigFragmentID(uuid4()),
            config_name="theme",
            scope_type=AppConfigScopeType.USER,
            scope_id=AppConfigScopeID(uuid4()),
            config={"color": "dark"},
            created_at=now,
            updated_at=now,
        )
        data = AppConfigData(
            config_name="theme",
            fragments=[first, second],
            merged_config={"color": "dark"},
        )

        node = AppConfigAdapter._app_config_to_node(data)

        assert node.config_name == "theme"
        assert node.merged_config == {"color": "dark"}
        assert [fragment.id for fragment in node.fragments] == [first.id, second.id]


class TestResolveAppConfigInput:
    def test_parses_nested_scope_arguments(self) -> None:
        domain_id = uuid4()

        parsed = ResolveAppConfigInput.model_validate({
            "config_names": ["theme"],
            "scope_arguments": {"domain_id": str(domain_id)},
        })

        assert parsed.config_names == ["theme"]
        assert parsed.scope_arguments.domain_id == domain_id

    def test_rejects_empty_config_names(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ResolveAppConfigInput.model_validate({
                "config_names": [],
                "scope_arguments": {"domain_id": str(uuid4())},
            })
