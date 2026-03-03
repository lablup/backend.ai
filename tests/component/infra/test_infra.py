from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.infra import (
    CheckPresetsRequest,
    CheckPresetsResponse,
    DeleteConfigRequest,
    DeleteConfigResponse,
    GetConfigRequest,
    GetConfigResponse,
    GetContainerRegistriesResponse,
    GetResourceMetadataResponse,
    GetResourceSlotsResponse,
    GetVFolderTypesResponse,
    ListPresetsRequest,
    ListPresetsResponse,
    ListScalingGroupsRequest,
    MonthStatsResponse,
    RecalculateUsageResponse,
    SetConfigRequest,
    SetConfigResponse,
    UsagePerMonthRequest,
    UsagePerMonthResponse,
    UsagePerPeriodRequest,
    UsagePerPeriodResponse,
)

_HMAC_XFAIL_REASON = (
    "Client SDK v2 HMAC signing omits query params; "
    "server verifies against request.raw_path (including ?param=...). "
    "Endpoints passing query params cause 401."
)

_GET_JSON_BODY_XFAIL_REASON = (
    "Client SDK v2 sends JSON body on GET requests, but the server's "
    "check_api_params reads from request.query for GET/HEAD methods, "
    "ignoring the body entirely.  Params are never seen by the server."
)


class TestEtcdConfigRead:
    """Tests for read-only etcd config endpoints (no auth required)."""

    async def test_admin_gets_resource_slots(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can fetch the system-wide known resource slots."""
        result = await admin_registry.infra.get_resource_slots()
        assert isinstance(result, GetResourceSlotsResponse)
        assert isinstance(result.root, dict)
        assert "cpu" in result.root
        assert "mem" in result.root

    async def test_admin_gets_resource_metadata(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can fetch resource slot metadata (accelerator info)."""
        result = await admin_registry.infra.get_resource_metadata()
        assert isinstance(result, GetResourceMetadataResponse)
        assert isinstance(result.root, dict)

    async def test_admin_gets_vfolder_types(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can fetch available virtual folder types."""
        result = await admin_registry.infra.get_vfolder_types()
        assert isinstance(result, GetVFolderTypesResponse)
        assert isinstance(result.root, list)
        assert "user" in result.root


class TestEtcdConfigCRUD:
    """Tests for etcd config CRUD endpoints (superadmin only)."""

    async def test_admin_sets_and_gets_config(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can set an etcd key and read it back."""
        test_key = f"test/infra-component/{uuid.uuid4().hex[:8]}"
        try:
            set_result = await admin_registry.infra.set_config(
                SetConfigRequest(key=test_key, value="test-value")
            )
            assert isinstance(set_result, SetConfigResponse)
            assert set_result.result == "ok"

            get_result = await admin_registry.infra.get_config(GetConfigRequest(key=test_key))
            assert isinstance(get_result, GetConfigResponse)
            assert get_result.result == "test-value"
        finally:
            await admin_registry.infra.delete_config(DeleteConfigRequest(key=test_key))

    async def test_admin_sets_and_deletes_config(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can set an etcd key, delete it, and verify it is gone."""
        test_key = f"test/infra-component/{uuid.uuid4().hex[:8]}"
        await admin_registry.infra.set_config(SetConfigRequest(key=test_key, value="to-delete"))

        delete_result = await admin_registry.infra.delete_config(DeleteConfigRequest(key=test_key))
        assert isinstance(delete_result, DeleteConfigResponse)
        assert delete_result.result == "ok"

        get_result = await admin_registry.infra.get_config(GetConfigRequest(key=test_key))
        assert get_result.result is None

    async def test_admin_gets_config_with_prefix(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can read multiple keys under a common prefix."""
        prefix = f"test/infra-prefix/{uuid.uuid4().hex[:8]}"
        try:
            await admin_registry.infra.set_config(
                SetConfigRequest(key=f"{prefix}/key1", value="val1")
            )
            await admin_registry.infra.set_config(
                SetConfigRequest(key=f"{prefix}/key2", value="val2")
            )

            get_result = await admin_registry.infra.get_config(
                GetConfigRequest(key=prefix, prefix=True)
            )
            assert isinstance(get_result, GetConfigResponse)
            assert isinstance(get_result.result, dict)
            assert get_result.result.get("key1") == "val1"
            assert get_result.result.get("key2") == "val2"
        finally:
            await admin_registry.infra.delete_config(DeleteConfigRequest(key=prefix, prefix=True))

    async def test_regular_user_cannot_get_config(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular users are blocked from reading etcd config (superadmin only)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.infra.get_config(GetConfigRequest(key="test/any-key"))

    async def test_regular_user_cannot_set_config(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular users are blocked from writing etcd config (superadmin only)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.infra.set_config(
                SetConfigRequest(key="test/any-key", value="any-value")
            )

    async def test_regular_user_cannot_delete_config(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular users are blocked from deleting etcd config (superadmin only)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.infra.delete_config(DeleteConfigRequest(key="test/any-key"))


class TestContainerRegistries:
    """Tests for container registry listing endpoint (superadmin only)."""

    async def test_admin_gets_container_registries(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can fetch the list of registered container registries."""
        result = await admin_registry.infra.get_container_registries()
        assert isinstance(result, GetContainerRegistriesResponse)
        assert isinstance(result.root, dict)

    async def test_regular_user_cannot_get_container_registries(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular users are blocked from listing container registries (superadmin only)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.infra.get_container_registries()


class TestResourcePresets:
    """Tests for resource preset endpoints."""

    async def test_admin_lists_presets(
        self,
        admin_registry: BackendAIClientRegistry,
        resource_preset_fixture: dict[str, str],
    ) -> None:
        """Admin can list resource presets; the fixture preset is included."""
        result = await admin_registry.infra.list_presets()
        assert isinstance(result, ListPresetsResponse)
        assert isinstance(result.presets, list)
        preset_names = [p["name"] for p in result.presets]
        assert resource_preset_fixture["name"] in preset_names

    async def test_admin_lists_presets_without_any(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can list presets even when no custom presets exist."""
        result = await admin_registry.infra.list_presets()
        assert isinstance(result, ListPresetsResponse)
        assert isinstance(result.presets, list)

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "check-presets response returns double-serialized JSON strings"
            " for resource slot fields - tracked separately"
        ),
    )
    async def test_admin_checks_presets(
        self,
        admin_registry: BackendAIClientRegistry,
        resource_preset_fixture: dict[str, str],
        group_name_fixture: str,
    ) -> None:
        """Admin can check presets with allocatability information."""
        result = await admin_registry.infra.check_presets(
            CheckPresetsRequest(group=group_name_fixture)
        )
        assert isinstance(result, CheckPresetsResponse)
        assert isinstance(result.presets, list)
        assert isinstance(result.keypair_limits, dict)
        assert isinstance(result.keypair_using, dict)
        assert isinstance(result.keypair_remaining, dict)
        assert isinstance(result.group_limits, dict)
        assert isinstance(result.group_using, dict)
        assert isinstance(result.group_remaining, dict)
        assert isinstance(result.scaling_group_remaining, dict)
        assert isinstance(result.scaling_groups, dict)

    @pytest.mark.xfail(reason=_HMAC_XFAIL_REASON, strict=True)
    async def test_list_presets_with_scaling_group_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Filtering presets by scaling group triggers HMAC bug (query params not signed)."""
        await admin_registry.infra.list_presets(
            ListPresetsRequest(scaling_group=scaling_group_fixture)
        )


class TestUsageStats:
    """Tests for usage statistics endpoints."""

    @pytest.mark.xfail(reason=_GET_JSON_BODY_XFAIL_REASON, strict=True)
    async def test_admin_gets_usage_per_month(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can query usage statistics for a given month."""
        result = await admin_registry.infra.get_usage_per_month(
            UsagePerMonthRequest(group_ids=[], month="202601")
        )
        assert isinstance(result, UsagePerMonthResponse)
        assert isinstance(result.root, list)

    @pytest.mark.xfail(reason=_GET_JSON_BODY_XFAIL_REASON, strict=True)
    async def test_admin_gets_usage_per_period(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can query usage statistics for a date range."""
        result = await admin_registry.infra.get_usage_per_period(
            UsagePerPeriodRequest(start_date="20260101", end_date="20260131")
        )
        assert isinstance(result, UsagePerPeriodResponse)
        assert isinstance(result.root, list)

    async def test_admin_recalculates_usage(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can trigger a usage recalculation."""
        result = await admin_registry.infra.recalculate_usage()
        assert isinstance(result, RecalculateUsageResponse)

    async def test_admin_gets_admin_month_stats(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can fetch admin-scoped monthly statistics."""
        result = await admin_registry.infra.get_admin_month_stats()
        assert isinstance(result, MonthStatsResponse)
        assert isinstance(result.root, list)

    async def test_user_gets_user_month_stats(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user can fetch their own monthly statistics (auth_required, not superadmin)."""
        result = await user_registry.infra.get_user_month_stats()
        assert isinstance(result, MonthStatsResponse)
        assert isinstance(result.root, list)

    async def test_regular_user_cannot_get_usage_per_month(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular users are blocked from admin usage stats (superadmin only)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.infra.get_usage_per_month(
                UsagePerMonthRequest(group_ids=[], month="202601")
            )

    async def test_regular_user_cannot_recalculate_usage(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular users are blocked from recalculating usage (superadmin only)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.infra.recalculate_usage()


class TestScalingGroupsViaInfra:
    """Tests for scaling group endpoints accessed via InfraClient."""

    @pytest.mark.xfail(reason=_HMAC_XFAIL_REASON, strict=True)
    async def test_admin_lists_scaling_groups_via_infra(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """InfraClient.list_scaling_groups triggers HMAC bug (query params not signed)."""
        await admin_registry.infra.list_scaling_groups(
            ListScalingGroupsRequest(group=str(group_fixture))
        )
