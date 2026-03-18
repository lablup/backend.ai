"""Tests for ai.backend.common.dto.manager.v2.artifact_registry.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.dto.manager.v2.artifact_registry.request import (
    ArtifactFilterInput,
    ArtifactOrderingInput,
    BackwardPaginationInput,
    DelegateeTargetInput,
    DelegateImportArtifactsInput,
    DelegateScanArtifactsInput,
    ForwardPaginationInput,
    ImportArtifactsOptionsInput,
    OffsetPaginationInput,
    PaginationInput,
    ScanArtifactModelsInput,
    ScanArtifactsInput,
    SearchArtifactsInput,
)
from ai.backend.common.dto.manager.v2.artifact_registry.types import ArtifactRegistryType


class TestForwardPaginationInput:
    """Tests for ForwardPaginationInput model."""

    def test_defaults_are_none(self) -> None:
        p = ForwardPaginationInput()
        assert p.after is None
        assert p.first is None

    def test_with_values(self) -> None:
        p = ForwardPaginationInput(after="cursor123", first=10)
        assert p.after == "cursor123"
        assert p.first == 10

    def test_round_trip_serialization(self) -> None:
        p = ForwardPaginationInput(after="cursor-abc", first=5)
        json_str = p.model_dump_json()
        restored = ForwardPaginationInput.model_validate_json(json_str)
        assert restored.after == "cursor-abc"
        assert restored.first == 5


class TestBackwardPaginationInput:
    """Tests for BackwardPaginationInput model."""

    def test_defaults_are_none(self) -> None:
        p = BackwardPaginationInput()
        assert p.before is None
        assert p.last is None

    def test_with_values(self) -> None:
        p = BackwardPaginationInput(before="cursor123", last=20)
        assert p.before == "cursor123"
        assert p.last == 20

    def test_round_trip_serialization(self) -> None:
        p = BackwardPaginationInput(before="cursor-xyz", last=15)
        json_str = p.model_dump_json()
        restored = BackwardPaginationInput.model_validate_json(json_str)
        assert restored.before == "cursor-xyz"
        assert restored.last == 15


class TestOffsetPaginationInput:
    """Tests for OffsetPaginationInput model."""

    def test_defaults_are_none(self) -> None:
        p = OffsetPaginationInput()
        assert p.offset is None
        assert p.limit is None

    def test_with_values(self) -> None:
        p = OffsetPaginationInput(offset=20, limit=10)
        assert p.offset == 20
        assert p.limit == 10

    def test_round_trip_serialization(self) -> None:
        p = OffsetPaginationInput(offset=0, limit=50)
        json_str = p.model_dump_json()
        restored = OffsetPaginationInput.model_validate_json(json_str)
        assert restored.offset == 0
        assert restored.limit == 50


class TestPaginationInput:
    """Tests for PaginationInput model."""

    def test_all_defaults_are_none(self) -> None:
        p = PaginationInput()
        assert p.forward is None
        assert p.backward is None
        assert p.offset is None

    def test_with_forward_pagination(self) -> None:
        fwd = ForwardPaginationInput(after="cursor", first=10)
        p = PaginationInput(forward=fwd)
        assert p.forward is not None
        assert p.forward.first == 10

    def test_with_offset_pagination(self) -> None:
        off = OffsetPaginationInput(offset=0, limit=20)
        p = PaginationInput(offset=off)
        assert p.offset is not None
        assert p.offset.limit == 20

    def test_round_trip_serialization(self) -> None:
        fwd = ForwardPaginationInput(after="cursor-a", first=5)
        p = PaginationInput(forward=fwd)
        json_str = p.model_dump_json()
        restored = PaginationInput.model_validate_json(json_str)
        assert restored.forward is not None
        assert restored.forward.after == "cursor-a"


class TestArtifactOrderingInput:
    """Tests for ArtifactOrderingInput model."""

    def test_default_order_by(self) -> None:
        o = ArtifactOrderingInput()
        assert o.order_by == [("NAME", False)]

    def test_custom_order_by(self) -> None:
        o = ArtifactOrderingInput(order_by=[("SIZE", True)])
        assert o.order_by == [("SIZE", True)]

    def test_multiple_order_by(self) -> None:
        o = ArtifactOrderingInput(order_by=[("NAME", False), ("SIZE", True)])
        assert len(o.order_by) == 2


class TestArtifactFilterInput:
    """Tests for ArtifactFilterInput model."""

    def test_all_defaults_are_none(self) -> None:
        f = ArtifactFilterInput()
        assert f.artifact_type is None
        assert f.name_filter is None
        assert f.registry_id is None
        assert f.AND is None
        assert f.OR is None
        assert f.NOT is None

    def test_with_registry_type(self) -> None:
        f = ArtifactFilterInput(registry_type=ArtifactRegistryType.HUGGINGFACE)
        assert f.registry_type == ArtifactRegistryType.HUGGINGFACE

    def test_with_nested_and_filter(self) -> None:
        inner = ArtifactFilterInput(registry_type=ArtifactRegistryType.RESERVOIR)
        f = ArtifactFilterInput(AND=[inner])
        assert f.AND is not None
        assert len(f.AND) == 1
        assert f.AND[0].registry_type == ArtifactRegistryType.RESERVOIR

    def test_with_registry_id(self) -> None:
        reg_id = uuid.uuid4()
        f = ArtifactFilterInput(registry_id=reg_id)
        assert f.registry_id == reg_id

    def test_with_artifact_type_list(self) -> None:
        f = ArtifactFilterInput(artifact_type=["MODEL", "PACKAGE"])
        assert f.artifact_type == ["MODEL", "PACKAGE"]


class TestImportArtifactsOptionsInput:
    """Tests for ImportArtifactsOptionsInput model."""

    def test_force_default_is_false(self) -> None:
        o = ImportArtifactsOptionsInput()
        assert o.force is False

    def test_force_true(self) -> None:
        o = ImportArtifactsOptionsInput(force=True)
        assert o.force is True


class TestDelegateeTargetInput:
    """Tests for DelegateeTargetInput model."""

    def test_basic_creation(self) -> None:
        delegatee_id = uuid.uuid4()
        target_id = uuid.uuid4()
        t = DelegateeTargetInput(delegatee_reservoir_id=delegatee_id, target_registry_id=target_id)
        assert t.delegatee_reservoir_id == delegatee_id
        assert t.target_registry_id == target_id

    def test_missing_fields_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DelegateeTargetInput.model_validate({})


class TestScanArtifactsInput:
    """Tests for ScanArtifactsInput model."""

    def test_basic_creation_with_limit(self) -> None:
        req = ScanArtifactsInput(limit=10)
        assert req.limit == 10
        assert req.registry_id is None
        assert req.artifact_type is None
        assert req.order is None
        assert req.search is None

    def test_with_registry_id(self) -> None:
        reg_id = uuid.uuid4()
        req = ScanArtifactsInput(registry_id=reg_id, limit=5)
        assert req.registry_id == reg_id

    def test_missing_limit_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ScanArtifactsInput.model_validate({})

    def test_round_trip_serialization(self) -> None:
        req = ScanArtifactsInput(limit=20, search="bert")
        json_str = req.model_dump_json()
        restored = ScanArtifactsInput.model_validate_json(json_str)
        assert restored.limit == 20
        assert restored.search == "bert"


class TestDelegateScanArtifactsInput:
    """Tests for DelegateScanArtifactsInput model."""

    def test_basic_creation(self) -> None:
        req = DelegateScanArtifactsInput(limit=10)
        assert req.limit == 10
        assert req.delegator_reservoir_id is None
        assert req.delegatee_target is None

    def test_with_delegation_ids(self) -> None:
        delegatee_id = uuid.uuid4()
        target_id = uuid.uuid4()
        delegatee = DelegateeTargetInput(
            delegatee_reservoir_id=delegatee_id,
            target_registry_id=target_id,
        )
        req = DelegateScanArtifactsInput(limit=5, delegatee_target=delegatee)
        assert req.delegatee_target is not None
        assert req.delegatee_target.delegatee_reservoir_id == delegatee_id


class TestDelegateImportArtifactsInput:
    """Tests for DelegateImportArtifactsInput model."""

    def test_basic_creation(self) -> None:
        rev_ids = [uuid.uuid4(), uuid.uuid4()]
        req = DelegateImportArtifactsInput(artifact_revision_ids=rev_ids)
        assert len(req.artifact_revision_ids) == 2
        assert req.delegator_reservoir_id is None
        assert req.delegatee_target is None

    def test_options_default(self) -> None:
        rev_ids = [uuid.uuid4()]
        req = DelegateImportArtifactsInput(artifact_revision_ids=rev_ids)
        assert req.options.force is False

    def test_with_force_options(self) -> None:
        rev_ids = [uuid.uuid4()]
        options = ImportArtifactsOptionsInput(force=True)
        req = DelegateImportArtifactsInput(artifact_revision_ids=rev_ids, options=options)
        assert req.options.force is True

    def test_missing_revision_ids_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            DelegateImportArtifactsInput.model_validate({})


class TestSearchArtifactsInput:
    """Tests for SearchArtifactsInput model."""

    def test_basic_creation_with_pagination(self) -> None:
        pagination = PaginationInput(offset=OffsetPaginationInput(offset=0, limit=10))
        req = SearchArtifactsInput(pagination=pagination)
        assert req.pagination.offset is not None
        assert req.ordering is None
        assert req.filters is None

    def test_with_ordering(self) -> None:
        pagination = PaginationInput()
        ordering = ArtifactOrderingInput(order_by=[("SIZE", True)])
        req = SearchArtifactsInput(pagination=pagination, ordering=ordering)
        assert req.ordering is not None
        assert req.ordering.order_by == [("SIZE", True)]

    def test_missing_pagination_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchArtifactsInput.model_validate({})

    def test_round_trip_serialization(self) -> None:
        pagination = PaginationInput(forward=ForwardPaginationInput(after="cursor", first=10))
        req = SearchArtifactsInput(pagination=pagination)
        json_str = req.model_dump_json()
        restored = SearchArtifactsInput.model_validate_json(json_str)
        assert restored.pagination.forward is not None
        assert restored.pagination.forward.after == "cursor"


class TestScanArtifactModelsInput:
    """Tests for ScanArtifactModelsInput model."""

    def test_basic_creation_with_models(self) -> None:
        model = ModelTarget(model_id="bert-base-uncased", revision="main")
        req = ScanArtifactModelsInput(models=[model])
        assert len(req.models) == 1
        assert req.registry_id is None

    def test_with_registry_id(self) -> None:
        reg_id = uuid.uuid4()
        model = ModelTarget(model_id="openai/gpt-2", revision=None)
        req = ScanArtifactModelsInput(models=[model], registry_id=reg_id)
        assert req.registry_id == reg_id

    def test_missing_models_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            ScanArtifactModelsInput.model_validate({})
