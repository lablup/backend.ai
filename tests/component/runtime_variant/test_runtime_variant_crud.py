"""Component tests for runtime variant v2 CRUD.

Test matrix:
  - Search: returns seed data
  - Search with filter: name-contains filter works
  - Create: creates a new runtime variant
  - Get: retrieves by ID
  - Update: modifies description
  - Delete: removes runtime variant
  - Duplicate name: returns 409 conflict
  - reads_vfolder_config_files + default_model_definition round-trip
"""

from __future__ import annotations

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelConfigInput,
    ModelDefinitionInput,
    ModelServiceConfigInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    CreateRuntimeVariantInput,
    RuntimeVariantFilter,
    SearchRuntimeVariantsInput,
    UpdateRuntimeVariantInput,
)


class TestRuntimeVariantSearch:
    """Tests for runtime variant search via POST /v2/runtime-variants/search."""

    async def test_search_returns_items(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Search should return runtime variants (seed data may or may not exist)."""
        result = await admin_v2_registry.runtime_variant.search(
            SearchRuntimeVariantsInput(limit=10, offset=0)
        )
        assert result.total_count >= 0
        assert isinstance(result.items, list)

    async def test_search_with_name_filter(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Search with name filter should narrow results."""
        # First create a variant to search for
        create_result = await admin_v2_registry.runtime_variant.create(
            CreateRuntimeVariantInput(name="filter-test-variant", description="For filter test")
        )
        variant_id = create_result.runtime_variant.id

        try:
            result = await admin_v2_registry.runtime_variant.search(
                SearchRuntimeVariantsInput(
                    filter=RuntimeVariantFilter(
                        name=StringFilter(contains="filter-test"),
                    ),
                    limit=10,
                    offset=0,
                )
            )
            assert result.total_count >= 1
            names = [item.name for item in result.items]
            assert "filter-test-variant" in names
        finally:
            await admin_v2_registry.runtime_variant.delete(variant_id)


class TestRuntimeVariantCRUD:
    """Tests for runtime variant create/get/update/delete."""

    async def test_create_and_get(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Create a runtime variant and retrieve it by ID."""
        create_result = await admin_v2_registry.runtime_variant.create(
            CreateRuntimeVariantInput(name="crud-test-variant", description="CRUD test")
        )
        variant = create_result.runtime_variant
        assert variant.name == "crud-test-variant"
        assert variant.description == "CRUD test"
        assert variant.id is not None

        try:
            get_result = await admin_v2_registry.runtime_variant.get(variant.id)
            assert get_result.id == variant.id
            assert get_result.name == "crud-test-variant"
        finally:
            await admin_v2_registry.runtime_variant.delete(variant.id)

    async def test_update(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Update a runtime variant's description."""
        create_result = await admin_v2_registry.runtime_variant.create(
            CreateRuntimeVariantInput(name="update-test-variant", description="Before update")
        )
        variant_id = create_result.runtime_variant.id

        try:
            update_result = await admin_v2_registry.runtime_variant.update(
                variant_id,
                UpdateRuntimeVariantInput(
                    id=variant_id,
                    description="After update",
                ),
            )
            assert update_result.runtime_variant.description == "After update"
            assert update_result.runtime_variant.updated_at is not None
        finally:
            await admin_v2_registry.runtime_variant.delete(variant_id)

    async def test_delete(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Delete a runtime variant."""
        create_result = await admin_v2_registry.runtime_variant.create(
            CreateRuntimeVariantInput(name="delete-test-variant")
        )
        variant_id = create_result.runtime_variant.id

        delete_result = await admin_v2_registry.runtime_variant.delete(variant_id)
        assert delete_result.id == variant_id

    async def test_duplicate_name_conflict(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Creating a runtime variant with duplicate name should fail with 409."""
        create_result = await admin_v2_registry.runtime_variant.create(
            CreateRuntimeVariantInput(name="dup-test-variant")
        )
        variant_id = create_result.runtime_variant.id

        try:
            with pytest.raises(BackendAPIError) as exc_info:
                await admin_v2_registry.runtime_variant.create(
                    CreateRuntimeVariantInput(name="dup-test-variant")
                )
            assert exc_info.value.args[0] == 409
        finally:
            await admin_v2_registry.runtime_variant.delete(variant_id)


class TestRuntimeVariantExtendedFields:
    """Round-trip tests for ``reads_vfolder_config_files`` and ``default_model_definition``."""

    async def test_create_without_fields_uses_empty_draft(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Default create should succeed with an empty draft baseline."""
        create_result = await admin_v2_registry.runtime_variant.create(
            CreateRuntimeVariantInput(name="default-fields-variant")
        )
        variant = create_result.runtime_variant
        try:
            assert variant.reads_vfolder_config_files is False
            assert variant.default_model_definition == {"models": None}
        finally:
            await admin_v2_registry.runtime_variant.delete(variant.id)

    async def test_create_with_fields(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Create with both fields should round-trip through GET."""
        definition = ModelDefinitionInput(
            models=[
                ModelConfigInput(
                    name="my-model",
                    service=ModelServiceConfigInput(port=8000),
                ),
            ],
        )
        create_result = await admin_v2_registry.runtime_variant.create(
            CreateRuntimeVariantInput(
                name="with-fields-variant",
                reads_vfolder_config_files=True,
                default_model_definition=definition,
            )
        )
        variant = create_result.runtime_variant
        try:
            assert variant.reads_vfolder_config_files is True
            models = variant.default_model_definition["models"]
            assert isinstance(models, list)
            assert models[0]["name"] == "my-model"
            assert models[0]["service"]["port"] == 8000

            fetched = await admin_v2_registry.runtime_variant.get(variant.id)
            assert fetched.reads_vfolder_config_files is True
            assert fetched.default_model_definition == variant.default_model_definition
        finally:
            await admin_v2_registry.runtime_variant.delete(variant.id)

    async def test_update_fields(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Update should change ``reads_vfolder_config_files`` and ``default_model_definition``."""
        create_result = await admin_v2_registry.runtime_variant.create(
            CreateRuntimeVariantInput(name="update-fields-variant")
        )
        variant_id = create_result.runtime_variant.id

        try:
            new_definition = ModelDefinitionInput(
                models=[
                    ModelConfigInput(
                        name="updated-model",
                        service=ModelServiceConfigInput(port=9000),
                    ),
                ],
            )
            update_result = await admin_v2_registry.runtime_variant.update(
                variant_id,
                UpdateRuntimeVariantInput(
                    id=variant_id,
                    reads_vfolder_config_files=True,
                    default_model_definition=new_definition,
                ),
            )
            updated = update_result.runtime_variant
            assert updated.reads_vfolder_config_files is True
            models = updated.default_model_definition["models"]
            assert isinstance(models, list)
            assert models[0]["name"] == "updated-model"
            assert models[0]["service"]["port"] == 9000
        finally:
            await admin_v2_registry.runtime_variant.delete(variant_id)

    async def test_update_omits_fields_keeps_existing(
        self,
        admin_v2_registry: V2ClientRegistry,
        database_fixture: None,
    ) -> None:
        """Omitting the new fields on update must leave them unchanged."""
        definition = ModelDefinitionInput(
            models=[
                ModelConfigInput(
                    name="keep-me",
                    service=ModelServiceConfigInput(port=7000),
                ),
            ],
        )
        create_result = await admin_v2_registry.runtime_variant.create(
            CreateRuntimeVariantInput(
                name="omit-fields-variant",
                reads_vfolder_config_files=True,
                default_model_definition=definition,
            )
        )
        variant_id = create_result.runtime_variant.id

        try:
            update_result = await admin_v2_registry.runtime_variant.update(
                variant_id,
                UpdateRuntimeVariantInput(
                    id=variant_id,
                    description="touch only description",
                ),
            )
            updated = update_result.runtime_variant
            assert updated.reads_vfolder_config_files is True
            assert updated.default_model_definition["models"][0]["name"] == "keep-me"
        finally:
            await admin_v2_registry.runtime_variant.delete(variant_id)
