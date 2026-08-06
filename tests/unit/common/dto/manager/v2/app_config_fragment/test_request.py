"""Tests for ai.backend.common.dto.manager.v2.app_config_fragment.request module."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentUpsertItem,
    AppConfigScopeRef,
    BulkPurgeAppConfigFragmentInput,
    MyBulkPurgeAppConfigFragmentsByNamesInput,
    MyUpsertAppConfigFragmentsInput,
    ScopedAppConfigFragmentsByNamesInput,
    ScopedBulkPurgeAppConfigFragmentsByNamesInput,
    ScopedUpsertAppConfigFragmentsInput,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID

_SCOPE_ID = AppConfigScopeID(uuid.UUID("11111111-1111-1111-1111-111111111111"))


@dataclass(frozen=True)
class _ScopeCase:
    scope_type: AppConfigScopeType
    scope_id: AppConfigScopeID | None


@pytest.fixture
def config_document() -> dict[str, Any]:
    return {"theme": {"mode": "dark"}, "banner": "hello"}


class TestUpsertAppConfigFragmentsInput:
    """The scope is named once for the whole batch, and its id must agree with its type."""

    @pytest.mark.parametrize(
        "case",
        [
            _ScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id=None),
            _ScopeCase(scope_type=AppConfigScopeType.DOMAIN, scope_id=_SCOPE_ID),
            _ScopeCase(scope_type=AppConfigScopeType.USER, scope_id=_SCOPE_ID),
        ],
        ids=lambda case: case.scope_type.value,
    )
    def test_scope_id_matching_its_scope_type_is_accepted(
        self, case: _ScopeCase, config_document: dict[str, Any]
    ) -> None:
        req = ScopedUpsertAppConfigFragmentsInput(
            scope=AppConfigScopeRef(scope_type=case.scope_type, scope_id=case.scope_id),
            items=[AppConfigFragmentUpsertItem(config_name="theme", config=config_document)],
        )

        assert req.scope.scope_type is case.scope_type
        assert req.scope.scope_id == case.scope_id

    @pytest.mark.parametrize(
        "case",
        [
            _ScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id=_SCOPE_ID),
            _ScopeCase(scope_type=AppConfigScopeType.DOMAIN, scope_id=None),
            _ScopeCase(scope_type=AppConfigScopeType.USER, scope_id=None),
        ],
        ids=lambda case: f"{case.scope_type.value}-{case.scope_id}",
    )
    def test_scope_id_disagreeing_with_its_scope_type_is_rejected(
        self, case: _ScopeCase, config_document: dict[str, Any]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ScopedUpsertAppConfigFragmentsInput.model_validate({
                "scope": {"scope_type": case.scope_type, "scope_id": case.scope_id},
                "items": [{"config_name": "theme", "config": config_document}],
            })

    @pytest.mark.parametrize(
        "scope_type",
        [AppConfigScopeType.DOMAIN, AppConfigScopeType.USER],
        ids=lambda scope_type: scope_type.value,
    )
    @pytest.mark.parametrize("scope_id", ["", "not-a-uuid"], ids=["empty", "malformed"])
    def test_scope_id_that_is_not_a_uuid_is_rejected(
        self, scope_type: AppConfigScopeType, scope_id: str, config_document: dict[str, Any]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ScopedUpsertAppConfigFragmentsInput.model_validate({
                "scope": {"scope_type": scope_type, "scope_id": scope_id},
                "items": [{"config_name": "theme", "config": config_document}],
            })

    def test_scope_id_defaults_to_none(self, config_document: dict[str, Any]) -> None:
        req = ScopedUpsertAppConfigFragmentsInput(
            scope=AppConfigScopeRef(scope_type=AppConfigScopeType.PUBLIC),
            items=[AppConfigFragmentUpsertItem(config_name="theme", config=config_document)],
        )

        assert req.scope.scope_id is None

    def test_an_empty_batch_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ScopedUpsertAppConfigFragmentsInput.model_validate({
                "scope": {"scope_type": AppConfigScopeType.PUBLIC},
                "items": [],
            })

    @pytest.mark.parametrize("config_name", ["", "x" * 129], ids=["empty", "too-long"])
    def test_config_name_outside_its_length_bounds_is_rejected(
        self, config_name: str, config_document: dict[str, Any]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            AppConfigFragmentUpsertItem.model_validate({
                "config_name": config_name,
                "config": config_document,
            })


class TestMyUpsertAppConfigFragmentsInput:
    """The self-service body carries no scope — the server resolves the acting user."""

    def test_items_alone_are_a_complete_body(self, config_document: dict[str, Any]) -> None:
        req = MyUpsertAppConfigFragmentsInput(
            items=[AppConfigFragmentUpsertItem(config_name="theme", config=config_document)]
        )

        assert len(req.items) == 1
        assert not hasattr(req, "scope_type")

    def test_an_empty_batch_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            MyUpsertAppConfigFragmentsInput.model_validate({"items": []})


class TestAppConfigFragmentsByNamesInput:
    """The by-names read names the scope like the upsert does, plus the config names to read."""

    def test_config_names_are_required(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ScopedAppConfigFragmentsByNamesInput.model_validate({
                "scope_type": AppConfigScopeType.PUBLIC,
                "config_names": [],
            })

    def test_scope_id_disagreeing_with_its_scope_type_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ScopedAppConfigFragmentsByNamesInput.model_validate({
                "scope_type": AppConfigScopeType.DOMAIN,
                "scope_id": None,
                "config_names": ["theme"],
            })


class TestScopedBulkPurgeAppConfigFragmentsByNamesInput:
    """The scoped purge names the scope like the by-names read does, plus the names to purge."""

    @pytest.mark.parametrize(
        "case",
        [
            _ScopeCase(scope_type=AppConfigScopeType.PUBLIC, scope_id=None),
            _ScopeCase(scope_type=AppConfigScopeType.DOMAIN, scope_id=_SCOPE_ID),
            _ScopeCase(scope_type=AppConfigScopeType.USER, scope_id=_SCOPE_ID),
        ],
        ids=lambda case: case.scope_type.value,
    )
    def test_scope_id_matching_its_scope_type_is_accepted(self, case: _ScopeCase) -> None:
        req = ScopedBulkPurgeAppConfigFragmentsByNamesInput(
            scope=AppConfigScopeRef(scope_type=case.scope_type, scope_id=case.scope_id),
            config_names=["theme"],
        )

        assert req.scope.scope_type is case.scope_type
        assert req.scope.scope_id == case.scope_id

    def test_scope_id_disagreeing_with_its_scope_type_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ScopedBulkPurgeAppConfigFragmentsByNamesInput.model_validate({
                "scope": {"scope_type": AppConfigScopeType.DOMAIN, "scope_id": None},
                "config_names": ["theme"],
            })

    def test_an_empty_batch_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ScopedBulkPurgeAppConfigFragmentsByNamesInput.model_validate({
                "scope": {"scope_type": AppConfigScopeType.PUBLIC, "scope_id": None},
                "config_names": [],
            })


class TestMyBulkPurgeAppConfigFragmentsByNamesInput:
    """The self-service purge names configs, not ids, and carries no scope."""

    def test_config_names_alone_are_a_complete_body(self) -> None:
        req = MyBulkPurgeAppConfigFragmentsByNamesInput(config_names=["theme"])

        assert req.config_names == ["theme"]
        assert not hasattr(req, "scope_type")

    def test_an_empty_batch_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            MyBulkPurgeAppConfigFragmentsByNamesInput.model_validate({"config_names": []})


class TestBulkPurgeAppConfigFragmentInput:
    """The bulk purge body rejects an empty batch rather than treating it as a no-op."""

    def test_bulk_purge_accepts_ids(self) -> None:
        fragment_id = AppConfigFragmentID(uuid.uuid4())

        req = BulkPurgeAppConfigFragmentInput(ids=[fragment_id])

        assert req.ids == [fragment_id]

    def test_bulk_purge_rejects_an_empty_batch(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            BulkPurgeAppConfigFragmentInput.model_validate({"ids": []})
