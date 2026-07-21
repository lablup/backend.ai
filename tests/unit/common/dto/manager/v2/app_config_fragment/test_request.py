"""Tests for ai.backend.common.dto.manager.v2.app_config_fragment.request module."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AppConfigFragmentUpdateItem,
    BulkPurgeAppConfigFragmentInput,
    BulkUpdateAppConfigFragmentInput,
    CreateAppConfigFragmentInput,
    UpdateAppConfigFragmentInput,
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


class TestCreateAppConfigFragmentInput:
    """Tests for the scope_id / scope_type agreement enforced by CreateAppConfigFragmentInput."""

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
        req = CreateAppConfigFragmentInput(
            config_name="theme",
            scope_type=case.scope_type,
            scope_id=case.scope_id,
            config=config_document,
        )

        assert req.scope_type is case.scope_type
        assert req.scope_id == case.scope_id

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
            CreateAppConfigFragmentInput.model_validate({
                "config_name": "theme",
                "scope_type": case.scope_type,
                "scope_id": case.scope_id,
                "config": config_document,
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
            CreateAppConfigFragmentInput.model_validate({
                "config_name": "theme",
                "scope_type": scope_type,
                "scope_id": scope_id,
                "config": config_document,
            })

    def test_scope_id_defaults_to_none(self, config_document: dict[str, Any]) -> None:
        req = CreateAppConfigFragmentInput(
            config_name="theme",
            scope_type=AppConfigScopeType.PUBLIC,
            config=config_document,
        )

        assert req.scope_id is None

    @pytest.mark.parametrize("config_name", ["", "x" * 129], ids=["empty", "too-long"])
    def test_config_name_outside_its_length_bounds_is_rejected(
        self, config_name: str, config_document: dict[str, Any]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            CreateAppConfigFragmentInput.model_validate({
                "config_name": config_name,
                "scope_type": AppConfigScopeType.PUBLIC,
                "config": config_document,
            })


class TestUpdateAppConfigFragmentInput:
    """The single-fragment update body carries no id — the request path identifies the target."""

    def test_config_alone_is_a_complete_body(self, config_document: dict[str, Any]) -> None:
        req = UpdateAppConfigFragmentInput(config=config_document)

        assert req.config == config_document
        assert not hasattr(req, "id")

    def test_config_is_required(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            UpdateAppConfigFragmentInput.model_validate({})


class TestAppConfigFragmentUpdateItem:
    """The bulk item does carry an id, since one request addresses many fragments."""

    def test_id_and_config_are_both_required(self, config_document: dict[str, Any]) -> None:
        fragment_id = AppConfigFragmentID(uuid.uuid4())

        item = AppConfigFragmentUpdateItem(id=fragment_id, config=config_document)

        assert item.id == fragment_id
        assert item.config == config_document

    def test_omitting_id_is_rejected(self, config_document: dict[str, Any]) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            AppConfigFragmentUpdateItem.model_validate({"config": config_document})


class TestBulkAppConfigFragmentInputs:
    """Both bulk bodies reject an empty batch rather than treating it as a no-op."""

    def test_bulk_update_accepts_items(self, config_document: dict[str, Any]) -> None:
        req = BulkUpdateAppConfigFragmentInput(
            items=[
                AppConfigFragmentUpdateItem(
                    id=AppConfigFragmentID(uuid.uuid4()), config=config_document
                )
            ]
        )

        assert len(req.items) == 1

    def test_bulk_update_rejects_an_empty_batch(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            BulkUpdateAppConfigFragmentInput.model_validate({"items": []})

    def test_bulk_purge_accepts_ids(self) -> None:
        fragment_id = AppConfigFragmentID(uuid.uuid4())

        req = BulkPurgeAppConfigFragmentInput(ids=[fragment_id])

        assert req.ids == [fragment_id]

    def test_bulk_purge_rejects_an_empty_batch(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            BulkPurgeAppConfigFragmentInput.model_validate({"ids": []})
