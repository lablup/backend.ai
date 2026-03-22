from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.infra import (
    DeleteConfigRequest,
    DeleteConfigResponse,
    GetConfigRequest,
    GetConfigResponse,
    GetResourceMetadataResponse,
    GetResourceSlotsResponse,
    GetVFolderTypesResponse,
    SetConfigRequest,
    SetConfigResponse,
)


class TestEtcdConfigCRUD:
    """Create -> read -> update -> delete integration flow for etcd config."""

    async def test_full_crud_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Set a key, read it, update it, delete it, verify gone."""
        test_key = f"test/etcd-config-component/{uuid.uuid4().hex[:8]}"
        try:
            # Create
            set_result = await admin_registry.infra.set_config(
                SetConfigRequest(key=test_key, value="initial-value")
            )
            assert isinstance(set_result, SetConfigResponse)
            assert set_result.result == "ok"

            # Read
            get_result = await admin_registry.infra.get_config(GetConfigRequest(key=test_key))
            assert isinstance(get_result, GetConfigResponse)
            assert get_result.result == "initial-value"

            # Update
            await admin_registry.infra.set_config(
                SetConfigRequest(key=test_key, value="updated-value")
            )
            get_result = await admin_registry.infra.get_config(GetConfigRequest(key=test_key))
            assert get_result.result == "updated-value"

            # Delete
            delete_result = await admin_registry.infra.delete_config(
                DeleteConfigRequest(key=test_key)
            )
            assert isinstance(delete_result, DeleteConfigResponse)
            assert delete_result.result == "ok"

            # Verify gone
            get_result = await admin_registry.infra.get_config(GetConfigRequest(key=test_key))
            assert get_result.result is None
        finally:
            # Cleanup in case of partial failure
            try:
                await admin_registry.infra.delete_config(DeleteConfigRequest(key=test_key))
            except Exception:
                pass

    async def test_prefix_read_and_delete(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Set multiple keys under a prefix, read with prefix, delete with prefix."""
        prefix = f"test/etcd-config-prefix/{uuid.uuid4().hex[:8]}"
        try:
            await admin_registry.infra.set_config(
                SetConfigRequest(key=f"{prefix}/a", value="val-a")
            )
            await admin_registry.infra.set_config(
                SetConfigRequest(key=f"{prefix}/b", value="val-b")
            )

            result = await admin_registry.infra.get_config(
                GetConfigRequest(key=prefix, prefix=True)
            )
            assert isinstance(result.result, dict)
            assert result.result.get("a") == "val-a"
            assert result.result.get("b") == "val-b"
        finally:
            await admin_registry.infra.delete_config(DeleteConfigRequest(key=prefix, prefix=True))

    async def test_delete_nonexistent_key_is_idempotent(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Deleting a key that does not exist should succeed (no error)."""
        test_key = f"test/etcd-config-nonexistent/{uuid.uuid4().hex[:8]}"
        result = await admin_registry.infra.delete_config(DeleteConfigRequest(key=test_key))
        assert isinstance(result, DeleteConfigResponse)
        assert result.result == "ok"

    async def test_regular_user_cannot_set_config(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular users are blocked from writing etcd config (superadmin only)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.infra.set_config(
                SetConfigRequest(key="test/unauthorized", value="any")
            )


class TestEtcdConfigResourceQueries:
    """Resource slots and metadata query tests."""

    async def test_get_resource_slots(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Returns dict containing known slots like cpu and mem."""
        result = await admin_registry.infra.get_resource_slots()
        assert isinstance(result, GetResourceSlotsResponse)
        assert isinstance(result.root, dict)
        assert "cpu" in result.root
        assert "mem" in result.root

    async def test_get_resource_metadata(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Returns metadata dict (may be empty without agents)."""
        result = await admin_registry.infra.get_resource_metadata()
        assert isinstance(result, GetResourceMetadataResponse)
        assert isinstance(result.root, dict)

    async def test_get_vfolder_types(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Returns configured vfolder type list."""
        result = await admin_registry.infra.get_vfolder_types()
        assert isinstance(result, GetVFolderTypesResponse)
        assert isinstance(result.root, list)
