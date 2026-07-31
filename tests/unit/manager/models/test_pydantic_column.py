"""Unit tests for ``PydanticColumn`` bind/result behavior."""

from __future__ import annotations

import pytest
from sqlalchemy.engine import Dialect
from sqlalchemy.engine.default import DefaultDialect

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.manager.models.base import PydanticColumn


class TestPydanticColumnExcludeUnset:
    @pytest.fixture
    def dialect(self) -> Dialect:
        # process_bind_param/process_result_value ignore the dialect.
        return DefaultDialect()

    @pytest.fixture
    def column(self) -> PydanticColumn[ModelDefinitionDraft]:
        return PydanticColumn(ModelDefinitionDraft, exclude_unset=True)

    @pytest.fixture
    def column_with_exclude_unset_false(self) -> PydanticColumn[ModelDefinitionDraft]:
        return PydanticColumn(ModelDefinitionDraft, exclude_unset=False)

    def test_round_trip_keeps_unset_fields_unset(
        self, column: PydanticColumn[ModelDefinitionDraft], dialect: Dialect
    ) -> None:
        draft = ModelDefinitionDraft.model_validate({"models": [{"service": {"port": 8080}}]})

        stored = column.process_bind_param(draft, dialect)
        loaded = column.process_result_value(stored, dialect)

        assert stored is not None
        assert "shell" not in stored["models"][0]["service"]
        assert loaded is not None
        assert loaded.models
        service = loaded.models[0].service
        assert service is not None
        assert "shell" not in service.model_fields_set

    def test_preserves_explicit_null(
        self, column: PydanticColumn[ModelDefinitionDraft], dialect: Dialect
    ) -> None:
        draft = ModelDefinitionDraft.model_validate({
            "models": [{"service": {"port": 8080, "shell": None}}]
        })

        stored = column.process_bind_param(draft, dialect)
        loaded = column.process_result_value(stored, dialect)

        assert stored is not None
        assert stored["models"][0]["service"]["shell"] is None
        assert loaded is not None
        assert loaded.models
        service = loaded.models[0].service
        assert service is not None
        assert "shell" in service.model_fields_set

    def test_default_dump_materializes_unset_fields_as_null(
        self,
        column_with_exclude_unset_false: PydanticColumn[ModelDefinitionDraft],
        dialect: Dialect,
    ) -> None:
        # Contrast case: without exclude_unset, unset fields are stored as explicit
        # nulls, and reloading marks them "explicitly set" — the legacy bug behavior.
        draft = ModelDefinitionDraft.model_validate({"models": [{"service": {"port": 8080}}]})

        stored = column_with_exclude_unset_false.process_bind_param(draft, dialect)
        loaded = column_with_exclude_unset_false.process_result_value(stored, dialect)

        assert stored is not None
        assert stored["models"][0]["service"]["shell"] is None
        assert loaded is not None
        assert loaded.models
        service = loaded.models[0].service
        assert service is not None
        assert "shell" in service.model_fields_set
        assert service.shell is None

    def test_copy_preserves_exclude_unset(
        self, column: PydanticColumn[ModelDefinitionDraft], dialect: Dialect
    ) -> None:
        # SQLAlchemy clones TypeDecorators internally; a copy() dropping the flag
        # would silently revert to materializing nulls.
        draft = ModelDefinitionDraft.model_validate({"models": [{"service": {"port": 8080}}]})

        stored = column.copy().process_bind_param(draft, dialect)

        assert stored is not None
        assert "shell" not in stored["models"][0]["service"]
