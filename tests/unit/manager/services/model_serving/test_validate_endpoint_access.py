"""
Unit tests for validate_endpoint_access function.

Tests verify access control logic for different user roles accessing endpoints.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from ai.backend.common.data.user.types import UserData
from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant
from ai.backend.manager.data.model_serving.types import (
    EndpointData,
    EndpointLifecycle,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.services.utils import validate_endpoint_access


@pytest.fixture
def base_endpoint_data() -> EndpointData:
    """Create a base EndpointData for testing."""
    return EndpointData(
        id=uuid.uuid4(),
        name="test-endpoint",
        image=None,
        domain="test-domain",
        project=uuid.uuid4(),
        resource_group="default",
        resource_slots=ResourceSlot({"cpu": "1", "mem": "1g"}),
        url="https://test-endpoint.example.com",
        model=uuid.uuid4(),
        model_definition_path=None,
        model_mount_destination=None,
        created_user_id=uuid.uuid4(),
        created_user_email="creator@example.com",
        session_owner_id=uuid.uuid4(),
        session_owner_email="owner@example.com",
        session_owner_role=UserRole.USER,
        tag=None,
        startup_command=None,
        bootstrap_script=None,
        callback_url=None,
        environ=None,
        resource_opts=None,
        replicas=1,
        cluster_mode=ClusterMode.SINGLE_NODE,
        cluster_size=1,
        open_to_public=False,
        created_at=datetime.now(tz=UTC),
        destroyed_at=None,
        retries=0,
        lifecycle_stage=EndpointLifecycle.CREATED,
        runtime_variant=RuntimeVariant.CUSTOM,
        extra_mounts=[],
        routings=None,
    )


class TestValidateEndpointAccessSuperadmin:
    """Tests for SUPERADMIN role access."""

    def test_superadmin_can_access_any_endpoint(self, base_endpoint_data: EndpointData) -> None:
        """SUPERADMIN should have access to any endpoint regardless of owner."""
        user_data = UserData(
            user_id=uuid.uuid4(),  # Different from owner
            is_authorized=True,
            is_admin=False,
            is_superadmin=True,
            role="superadmin",
            domain_name="other-domain",  # Different domain
        )

        assert validate_endpoint_access(base_endpoint_data, user_data)

    def test_superadmin_can_access_superadmin_owned_endpoint(
        self, base_endpoint_data: EndpointData
    ) -> None:
        """SUPERADMIN should access endpoints owned by other SUPERADMINs."""
        base_endpoint_data.session_owner_role = UserRole.SUPERADMIN

        user_data = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=True,
            role="superadmin",
            domain_name="other-domain",
        )

        assert validate_endpoint_access(base_endpoint_data, user_data)


class TestValidateEndpointAccessAdmin:
    """Tests for ADMIN role access."""

    def test_admin_can_access_endpoint_in_same_domain(
        self, base_endpoint_data: EndpointData
    ) -> None:
        """ADMIN should access endpoints in their domain owned by regular users."""
        base_endpoint_data.session_owner_role = UserRole.USER

        user_data = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=True,
            is_superadmin=False,
            role="admin",
            domain_name="test-domain",  # Same as endpoint
        )

        assert validate_endpoint_access(base_endpoint_data, user_data)

    def test_admin_cannot_access_endpoint_in_different_domain(
        self, base_endpoint_data: EndpointData
    ) -> None:
        """ADMIN should NOT access endpoints in different domains."""
        base_endpoint_data.session_owner_role = UserRole.USER

        user_data = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=True,
            is_superadmin=False,
            role="admin",
            domain_name="other-domain",  # Different from endpoint
        )

        assert not validate_endpoint_access(base_endpoint_data, user_data)

    def test_admin_cannot_access_superadmin_owned_endpoint(
        self, base_endpoint_data: EndpointData
    ) -> None:
        """ADMIN should NOT access endpoints owned by SUPERADMIN users.

        This is a critical security test - ADMIN users should never be able
        to access resources owned by SUPERADMIN users, even in the same domain.
        """
        base_endpoint_data.session_owner_role = UserRole.SUPERADMIN
        base_endpoint_data.domain = "test-domain"

        user_data = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=True,
            is_superadmin=False,
            role="admin",
            domain_name="test-domain",  # Same domain, but owner is SUPERADMIN
        )

        assert not validate_endpoint_access(base_endpoint_data, user_data)

    def test_admin_can_access_admin_owned_endpoint_in_same_domain(
        self, base_endpoint_data: EndpointData
    ) -> None:
        """ADMIN should access endpoints owned by other ADMINs in same domain."""
        base_endpoint_data.session_owner_role = UserRole.ADMIN

        user_data = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=True,
            is_superadmin=False,
            role="admin",
            domain_name="test-domain",
        )

        assert validate_endpoint_access(base_endpoint_data, user_data)


class TestValidateEndpointAccessUser:
    """Tests for regular USER role access."""

    def test_user_can_access_own_endpoint(self, base_endpoint_data: EndpointData) -> None:
        """USER should access their own endpoints."""
        owner_id = uuid.uuid4()
        base_endpoint_data.session_owner_id = owner_id

        user_data = UserData(
            user_id=owner_id,  # Same as owner
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role="user",
            domain_name="test-domain",
        )

        assert validate_endpoint_access(base_endpoint_data, user_data)

    def test_user_cannot_access_other_users_endpoint(
        self, base_endpoint_data: EndpointData
    ) -> None:
        """USER should NOT access other users' endpoints."""
        user_data = UserData(
            user_id=uuid.uuid4(),  # Different from owner
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role="user",
            domain_name="test-domain",
        )

        assert not validate_endpoint_access(base_endpoint_data, user_data)

    def test_user_cannot_access_endpoint_even_in_same_domain(
        self, base_endpoint_data: EndpointData
    ) -> None:
        """USER should NOT access other users' endpoints even in the same domain."""
        user_data = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role="user",
            domain_name="test-domain",  # Same domain doesn't matter for USER
        )

        assert not validate_endpoint_access(base_endpoint_data, user_data)


class TestValidateEndpointAccessMonitor:
    """Tests for MONITOR role access."""

    def test_monitor_can_access_own_endpoint(self, base_endpoint_data: EndpointData) -> None:
        """MONITOR should access their own endpoints."""
        owner_id = uuid.uuid4()
        base_endpoint_data.session_owner_id = owner_id

        user_data = UserData(
            user_id=owner_id,
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role="monitor",
            domain_name="test-domain",
        )

        assert validate_endpoint_access(base_endpoint_data, user_data)

    def test_monitor_cannot_access_other_users_endpoint(
        self, base_endpoint_data: EndpointData
    ) -> None:
        """MONITOR should NOT access other users' endpoints."""
        user_data = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role="monitor",
            domain_name="test-domain",
        )

        assert not validate_endpoint_access(base_endpoint_data, user_data)


class TestValidateEndpointAccessEdgeCases:
    """Tests for edge cases."""

    def test_endpoint_with_none_session_owner_role(self, base_endpoint_data: EndpointData) -> None:
        """ADMIN should access endpoints with None session_owner_role in same domain."""
        base_endpoint_data.session_owner_role = None

        user_data = UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=True,
            is_superadmin=False,
            role="admin",
            domain_name="test-domain",
        )

        # None != SUPERADMIN, so domain check applies
        assert validate_endpoint_access(base_endpoint_data, user_data)
