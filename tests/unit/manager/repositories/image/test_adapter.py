"""Unit tests for ImageCreatorAdapter."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from ai.backend.common.data.permission.types import GLOBAL_SCOPE_ID, EntityType, ScopeType
from ai.backend.common.docker import LabelName
from ai.backend.manager.repositories.image.adapter import ImageCreatorAdapter
from ai.backend.manager.repositories.image.creators import ImageRowCreatorSpec


class TestImageCreatorAdapter:
    """Tests for ImageCreatorAdapter scope resolution."""

    @pytest.fixture
    def adapter(self) -> ImageCreatorAdapter:
        return ImageCreatorAdapter()

    @pytest.fixture
    def base_spec_kwargs(self) -> dict[str, Any]:
        """Base kwargs for ImageRowCreatorSpec."""
        return {
            "name": "test-image",
            "project": None,
            "architecture": "x86_64",
            "registry_id": uuid4(),
        }

    @pytest.fixture
    def user_id(self) -> str:
        return str(uuid4())

    @pytest.fixture
    def spec_with_owner_label(
        self, base_spec_kwargs: dict[str, Any], user_id: str
    ) -> ImageRowCreatorSpec:
        """Spec with owner label for USER scope."""
        return ImageRowCreatorSpec(
            **base_spec_kwargs,
            labels={LabelName.CUSTOMIZED_OWNER: f"user:{user_id}"},
        )

    @pytest.fixture
    def spec_without_owner_label(self, base_spec_kwargs: dict[str, Any]) -> ImageRowCreatorSpec:
        """Spec with unrelated label for GLOBAL scope."""
        return ImageRowCreatorSpec(
            **base_spec_kwargs,
            labels={"other_label": "value"},
        )

    @pytest.fixture
    def spec_with_empty_labels(self, base_spec_kwargs: dict[str, Any]) -> ImageRowCreatorSpec:
        """Spec with empty labels dict for GLOBAL scope."""
        return ImageRowCreatorSpec(**base_spec_kwargs, labels={})

    @pytest.fixture
    def spec_with_none_labels(self, base_spec_kwargs: dict[str, Any]) -> ImageRowCreatorSpec:
        """Spec with None labels for GLOBAL scope."""
        return ImageRowCreatorSpec(**base_spec_kwargs, labels=None)

    def test_build_with_owner_label_returns_user_scope(
        self,
        adapter: ImageCreatorAdapter,
        spec_with_owner_label: ImageRowCreatorSpec,
        user_id: str,
    ) -> None:
        """Should return USER scope when owner label exists."""
        creator = adapter.build(spec_with_owner_label)

        assert creator.scope_type == ScopeType.USER
        assert creator.scope_id == user_id
        assert creator.entity_type == EntityType.IMAGE

    def test_build_without_owner_label_returns_global_scope(
        self,
        adapter: ImageCreatorAdapter,
        spec_without_owner_label: ImageRowCreatorSpec,
    ) -> None:
        """Should return GLOBAL scope when owner label is missing."""
        creator = adapter.build(spec_without_owner_label)

        assert creator.scope_type == ScopeType.GLOBAL
        assert creator.scope_id == GLOBAL_SCOPE_ID
        assert creator.entity_type == EntityType.IMAGE

    def test_build_with_empty_labels_returns_global_scope(
        self,
        adapter: ImageCreatorAdapter,
        spec_with_empty_labels: ImageRowCreatorSpec,
    ) -> None:
        """Should return GLOBAL scope when labels dict is empty."""
        creator = adapter.build(spec_with_empty_labels)

        assert creator.scope_type == ScopeType.GLOBAL
        assert creator.scope_id == GLOBAL_SCOPE_ID

    def test_build_with_none_labels_returns_global_scope(
        self,
        adapter: ImageCreatorAdapter,
        spec_with_none_labels: ImageRowCreatorSpec,
    ) -> None:
        """Should return GLOBAL scope when labels is None."""
        creator = adapter.build(spec_with_none_labels)

        assert creator.scope_type == ScopeType.GLOBAL
        assert creator.scope_id == GLOBAL_SCOPE_ID
