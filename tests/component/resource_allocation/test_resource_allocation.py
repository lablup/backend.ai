"""Component tests for resource allocation v2 REST API."""

from __future__ import annotations

import uuid

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    CheckPresetAvailabilityInput,
    EffectiveResourceAllocationInput,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    DomainResourceAllocationPayload,
    EffectiveResourceAllocationPayload,
    KeypairResourceAllocationPayload,
    ProjectResourceAllocationPayload,
    ResourceGroupResourceAllocationPayload,
)


class TestKeypairUsage:
    """Tests for the keypair usage endpoint (GET /v2/resource-allocation/keypair/my)."""

    async def test_admin_keypair_usage_returns_limits_and_used(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """Admin can query own keypair usage; response contains limits and used fields."""
        result = await admin_v2_registry.resource_allocation.my_keypair_usage()
        assert isinstance(result, KeypairResourceAllocationPayload)
        assert result.keypair is not None
        assert isinstance(result.keypair.limits, list)
        assert isinstance(result.keypair.used, list)
        assert isinstance(result.keypair.assignable, list)


class TestProjectUsage:
    """Tests for the project usage endpoint (GET /v2/resource-allocation/projects/{id})."""

    async def test_project_usage_returns_limits_and_used(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """Query project usage with a valid project ID returns correct structure."""
        result = await admin_v2_registry.resource_allocation.project_usage(group_fixture)
        assert isinstance(result, ProjectResourceAllocationPayload)
        assert result.project is not None
        assert isinstance(result.project.limits, list)
        assert isinstance(result.project.used, list)
        assert isinstance(result.project.assignable, list)

    async def test_invalid_project_id_returns_error(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """Query with a non-existent project UUID returns an error."""
        fake_id = uuid.uuid4()
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_v2_registry.resource_allocation.project_usage(fake_id)
        assert exc_info.value.status in (404, 500)


class TestDomainUsage:
    """Tests for the domain usage endpoint (GET /v2/resource-allocation/domains/{name})."""

    async def test_admin_domain_usage_returns_data(
        self,
        admin_v2_registry: V2ClientRegistry,
        domain_fixture: str,
    ) -> None:
        """Admin can query domain usage with valid domain name."""
        result = await admin_v2_registry.resource_allocation.admin_domain_usage(
            domain_fixture,
        )
        assert isinstance(result, DomainResourceAllocationPayload)
        assert result.domain is not None
        assert isinstance(result.domain.limits, list)
        assert isinstance(result.domain.used, list)
        assert isinstance(result.domain.assignable, list)

    async def test_regular_user_domain_usage_returns_403(
        self,
        user_v2_registry: V2ClientRegistry,
        domain_fixture: str,
    ) -> None:
        """Non-admin user gets 403 when querying domain usage (superadmin_required)."""
        with pytest.raises(BackendAPIError) as exc_info:
            await user_v2_registry.resource_allocation.admin_domain_usage(
                domain_fixture,
            )
        assert exc_info.value.status == 403


class TestResourceGroupUsage:
    """Tests for resource group usage (GET /v2/resource-allocation/resource-groups/{name})."""

    async def test_resource_group_usage_returns_structure(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Query resource group usage returns capacity, used, free, max_per_node fields."""
        result = await admin_v2_registry.resource_allocation.resource_group_usage(
            scaling_group_fixture,
        )
        assert isinstance(result, ResourceGroupResourceAllocationPayload)
        assert result.resource_group is not None
        assert isinstance(result.resource_group.capacity, list)
        assert isinstance(result.resource_group.used, list)
        assert isinstance(result.resource_group.free, list)
        assert isinstance(result.resource_group.max_per_node, list)

    async def test_invalid_rg_returns_error(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """Query a non-existent resource group returns an error."""
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_v2_registry.resource_allocation.resource_group_usage(
                "non-existent-rg-name",
            )
        assert exc_info.value.status in (404, 500)


class TestEffectiveAllocation:
    """Tests for effective allocation (POST /v2/resource-allocation/effective)."""

    async def test_effective_returns_assignable_and_breakdown(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        scaling_group_fixture: str,
    ) -> None:
        """Effective allocation returns assignable list and breakdown structure."""
        result = await admin_v2_registry.resource_allocation.effective(
            EffectiveResourceAllocationInput(
                project_id=group_fixture,
                resource_group_name=scaling_group_fixture,
            ),
        )
        assert isinstance(result, EffectiveResourceAllocationPayload)
        assert isinstance(result.assignable, list)
        assert result.breakdown is not None
        assert result.breakdown.keypair is not None
        assert result.breakdown.domain is not None

    async def test_effective_with_invalid_project_returns_error(
        self,
        admin_v2_registry: V2ClientRegistry,
        scaling_group_fixture: str,
    ) -> None:
        """Effective allocation with non-existent project returns an error."""
        fake_id = uuid.uuid4()
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_v2_registry.resource_allocation.effective(
                EffectiveResourceAllocationInput(
                    project_id=fake_id,
                    resource_group_name=scaling_group_fixture,
                ),
            )
        assert exc_info.value.status in (404, 500)


class TestPresetAvailability:
    """Tests for preset availability (POST /v2/resource-allocation/check-preset-availability)."""

    async def test_preset_availability_returns_list(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        scaling_group_fixture: str,
    ) -> None:
        """Check preset availability returns a list of presets with availability status."""
        result = await admin_v2_registry.resource_allocation.check_availability(
            CheckPresetAvailabilityInput(
                project_id=group_fixture,
                resource_group_name=scaling_group_fixture,
            ),
        )
        assert isinstance(result.presets, list)
        # Each preset node should have the expected fields
        for preset in result.presets:
            assert isinstance(preset.name, str)
            assert isinstance(preset.available, bool)
            assert isinstance(preset.resource_slots, list)
