"""Tests for ai.backend.common.dto.manager.v2.app_config_fragment.request module."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import AppConfigScopeID
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentPatch,
    AppConfigFragmentUpsertItem,
    AppConfigScopeRef,
    BulkPurgeAppConfigFragmentInput,
    MyPatchAppConfigFragmentsInput,
    MyUpsertAppConfigFragmentsInput,
    ScopedAppConfigFragmentsByNamesInput,
    ScopedUpsertAppConfigFragmentsInput,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed

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


class TestBulkPurgeAppConfigFragmentInput:
    """The bulk purge body rejects an empty batch rather than treating it as a no-op."""

    def test_bulk_purge_accepts_ids(self) -> None:
        fragment_id = AppConfigFragmentID(uuid.uuid4())

        req = BulkPurgeAppConfigFragmentInput(ids=[fragment_id])

        assert req.ids == [fragment_id]

    def test_bulk_purge_rejects_an_empty_batch(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            BulkPurgeAppConfigFragmentInput.model_validate({"ids": []})


class TestAppConfigFragmentPatch:
    """A patch names top-level keys to set and to unset, each key once."""

    def test_set_and_unset_are_accepted_together(self) -> None:
        patch = AppConfigFragmentPatch.model_validate({
            "config_name": "theme",
            "set": [{"key": "mode", "value": {"nested": [1, 2]}}],
            "unset": ["banner"],
        })

        assert [(entry.key, entry.value) for entry in patch.set or []] == [
            ("mode", {"nested": [1, 2]})
        ]
        assert patch.unset == ["banner"]

    def test_unset_alone_is_accepted(self) -> None:
        patch = AppConfigFragmentPatch.model_validate({"config_name": "theme", "unset": ["a"]})

        assert patch.set is None

    def test_a_key_is_never_read_as_a_path(self) -> None:
        patch = AppConfigFragmentPatch.model_validate({
            "config_name": "theme",
            "set": [{"key": "a.b", "value": 1}],
        })

        assert patch.set is not None
        assert patch.set[0].key == "a.b"

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param({"config_name": "theme"}, id="neither-set-nor-unset"),
            pytest.param({"config_name": "theme", "set": [], "unset": []}, id="both-empty"),
            pytest.param(
                {
                    "config_name": "theme",
                    "set": [{"key": "a", "value": 1}, {"key": "a", "value": 2}],
                },
                id="same-key-twice-in-set",
            ),
            pytest.param(
                {"config_name": "theme", "unset": ["a", "a"]}, id="same-key-twice-in-unset"
            ),
            pytest.param(
                {"config_name": "theme", "set": [{"key": "a", "value": 1}], "unset": ["a"]},
                id="same-key-in-set-and-unset",
            ),
            pytest.param(
                {"config_name": "theme", "set": [{"key": "", "value": 1}]}, id="empty-key"
            ),
        ],
    )
    def test_an_invalid_patch_is_rejected(self, body: dict[str, Any]) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            AppConfigFragmentPatch.model_validate(body)

    def test_an_empty_batch_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            MyPatchAppConfigFragmentsInput.model_validate({"items": []})
