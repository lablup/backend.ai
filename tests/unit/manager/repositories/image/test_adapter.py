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

    def test_build_with_owner_label_returns_user_scope(
        self,
        adapter: ImageCreatorAdapter,
        base_spec_kwargs: dict[str, Any],
        user_id: str,
    ) -> None:
        """Should return USER scope when owner label exists."""
        spec = ImageRowCreatorSpec(
            **base_spec_kwargs,
            labels={LabelName.CUSTOMIZED_OWNER: f"user:{user_id}"},
        )

        creator = adapter.build(spec)

        assert creator.scope_type == ScopeType.USER
        assert creator.scope_id == user_id
        assert creator.entity_type == EntityType.IMAGE

    def test_build_without_owner_label_returns_global_scope(
        self,
        adapter: ImageCreatorAdapter,
        base_spec_kwargs: dict[str, Any],
    ) -> None:
        """Should return GLOBAL scope when owner label is missing."""
        spec = ImageRowCreatorSpec(
            **base_spec_kwargs,
            labels={"other_label": "value"},
        )

        creator = adapter.build(spec)

        assert creator.scope_type == ScopeType.GLOBAL
        assert creator.scope_id == GLOBAL_SCOPE_ID
        assert creator.entity_type == EntityType.IMAGE

    def test_build_with_empty_labels_returns_global_scope(
        self,
        adapter: ImageCreatorAdapter,
        base_spec_kwargs: dict[str, Any],
    ) -> None:
        """Should return GLOBAL scope when labels dict is empty."""
        spec = ImageRowCreatorSpec(**base_spec_kwargs, labels={})

        creator = adapter.build(spec)

        assert creator.scope_type == ScopeType.GLOBAL
        assert creator.scope_id == GLOBAL_SCOPE_ID

    def test_build_with_none_labels_returns_global_scope(
        self,
        adapter: ImageCreatorAdapter,
        base_spec_kwargs: dict[str, Any],
    ) -> None:
        """Should return GLOBAL scope when labels is None."""
        spec = ImageRowCreatorSpec(**base_spec_kwargs, labels=None)

        creator = adapter.build(spec)

        assert creator.scope_type == ScopeType.GLOBAL
        assert creator.scope_id == GLOBAL_SCOPE_ID
