"""
Unit tests for validate_endpoint_access function.

Tests verify access control logic for different user roles accessing endpoints.
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.manager.data.model_serving.types import (
    EndpointAccessValidationData,
    RequesterCtx,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.services.utils import validate_endpoint_access


@pytest.fixture
def base_validation_data() -> EndpointAccessValidationData:
    """Create a base EndpointAccessValidationData for testing."""
    return EndpointAccessValidationData(
        session_owner_id=uuid.uuid4(),
        session_owner_role=UserRole.USER,
        domain="test-domain",
    )


class TestValidateEndpointAccessSuperadmin:
    """Tests for SUPERADMIN role access."""

    def test_superadmin_can_access_any_endpoint(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """SUPERADMIN should have access to any endpoint regardless of owner."""
        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),  # Different from owner
            user_role=UserRole.SUPERADMIN,
            domain_name="other-domain",  # Different domain
        )

        assert validate_endpoint_access(base_validation_data, ctx) is True

    def test_superadmin_can_access_superadmin_owned_endpoint(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """SUPERADMIN should access endpoints owned by other SUPERADMINs."""
        base_validation_data.session_owner_role = UserRole.SUPERADMIN

        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),
            user_role=UserRole.SUPERADMIN,
            domain_name="other-domain",
        )

        assert validate_endpoint_access(base_validation_data, ctx) is True


class TestValidateEndpointAccessAdmin:
    """Tests for ADMIN role access."""

    def test_admin_can_access_endpoint_in_same_domain(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """ADMIN should access endpoints in their domain owned by regular users."""
        base_validation_data.session_owner_role = UserRole.USER

        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),
            user_role=UserRole.ADMIN,
            domain_name="test-domain",  # Same as endpoint
        )

        assert validate_endpoint_access(base_validation_data, ctx) is True

    def test_admin_cannot_access_endpoint_in_different_domain(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """ADMIN should NOT access endpoints in different domains."""
        base_validation_data.session_owner_role = UserRole.USER

        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),
            user_role=UserRole.ADMIN,
            domain_name="other-domain",  # Different from endpoint
        )

        assert validate_endpoint_access(base_validation_data, ctx) is False

    def test_admin_cannot_access_superadmin_owned_endpoint(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """ADMIN should NOT access endpoints owned by SUPERADMIN users.

        This is a critical security test - ADMIN users should never be able
        to access resources owned by SUPERADMIN users, even in the same domain.
        """
        base_validation_data.session_owner_role = UserRole.SUPERADMIN
        base_validation_data.domain = "test-domain"

        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),
            user_role=UserRole.ADMIN,
            domain_name="test-domain",  # Same domain, but owner is SUPERADMIN
        )

        assert validate_endpoint_access(base_validation_data, ctx) is False

    def test_admin_can_access_admin_owned_endpoint_in_same_domain(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """ADMIN should access endpoints owned by other ADMINs in same domain."""
        base_validation_data.session_owner_role = UserRole.ADMIN

        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),
            user_role=UserRole.ADMIN,
            domain_name="test-domain",
        )

        assert validate_endpoint_access(base_validation_data, ctx) is True


class TestValidateEndpointAccessUser:
    """Tests for regular USER role access."""

    def test_user_can_access_own_endpoint(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """USER should access their own endpoints."""
        owner_id = uuid.uuid4()
        base_validation_data.session_owner_id = owner_id

        ctx = RequesterCtx(
            is_authorized=True,
            user_id=owner_id,  # Same as owner
            user_role=UserRole.USER,
            domain_name="test-domain",
        )

        assert validate_endpoint_access(base_validation_data, ctx) is True

    def test_user_cannot_access_other_users_endpoint(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """USER should NOT access other users' endpoints."""
        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),  # Different from owner
            user_role=UserRole.USER,
            domain_name="test-domain",
        )

        assert validate_endpoint_access(base_validation_data, ctx) is False

    def test_user_cannot_access_endpoint_even_in_same_domain(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """USER should NOT access other users' endpoints even in the same domain."""
        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),
            user_role=UserRole.USER,
            domain_name="test-domain",  # Same domain doesn't matter for USER
        )

        assert validate_endpoint_access(base_validation_data, ctx) is False


class TestValidateEndpointAccessMonitor:
    """Tests for MONITOR role access."""

    def test_monitor_can_access_own_endpoint(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """MONITOR should access their own endpoints."""
        owner_id = uuid.uuid4()
        base_validation_data.session_owner_id = owner_id

        ctx = RequesterCtx(
            is_authorized=True,
            user_id=owner_id,
            user_role=UserRole.MONITOR,
            domain_name="test-domain",
        )

        assert validate_endpoint_access(base_validation_data, ctx) is True

    def test_monitor_cannot_access_other_users_endpoint(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """MONITOR should NOT access other users' endpoints."""
        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),
            user_role=UserRole.MONITOR,
            domain_name="test-domain",
        )

        assert validate_endpoint_access(base_validation_data, ctx) is False


class TestValidateEndpointAccessEdgeCases:
    """Tests for edge cases."""

    def test_endpoint_with_none_session_owner_role(
        self, base_validation_data: EndpointAccessValidationData
    ) -> None:
        """ADMIN should access endpoints with None session_owner_role in same domain."""
        base_validation_data.session_owner_role = None

        ctx = RequesterCtx(
            is_authorized=True,
            user_id=uuid.uuid4(),
            user_role=UserRole.ADMIN,
            domain_name="test-domain",
        )

        # None != SUPERADMIN, so domain check applies
        assert validate_endpoint_access(base_validation_data, ctx) is True
