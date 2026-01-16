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


class ValidateEndpointAccessBaseFixtures:
    """Base class containing shared fixtures for validate_endpoint_access tests."""

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        """User ID for test fixtures."""
        return uuid.uuid4()

    @pytest.fixture
    def base_validation_data(self) -> EndpointAccessValidationData:
        """Create a base EndpointAccessValidationData for testing."""
        return EndpointAccessValidationData(
            session_owner_id=uuid.uuid4(),
            session_owner_role=UserRole.USER,
            domain="test-domain",
        )

    @pytest.fixture
    def superadmin_requester_ctx(self, user_id: uuid.UUID) -> RequesterCtx:
        """Create a SUPERADMIN RequesterCtx for testing."""
        return RequesterCtx(
            is_authorized=True,
            user_id=user_id,
            user_role=UserRole.SUPERADMIN,
            domain_name="other-domain",
        )

    @pytest.fixture
    def admin_requester_ctx(self, user_id: uuid.UUID) -> RequesterCtx:
        """Create an ADMIN RequesterCtx for testing."""
        return RequesterCtx(
            is_authorized=True,
            user_id=user_id,
            user_role=UserRole.ADMIN,
            domain_name="test-domain",
        )

    @pytest.fixture
    def user_requester_ctx(self, user_id: uuid.UUID) -> RequesterCtx:
        """Create a USER RequesterCtx for testing."""
        return RequesterCtx(
            is_authorized=True,
            user_id=user_id,
            user_role=UserRole.USER,
            domain_name="test-domain",
        )

    @pytest.fixture
    def monitor_requester_ctx(self, user_id: uuid.UUID) -> RequesterCtx:
        """Create a MONITOR RequesterCtx for testing."""
        return RequesterCtx(
            is_authorized=True,
            user_id=user_id,
            user_role=UserRole.MONITOR,
            domain_name="test-domain",
        )


class TestValidateEndpointAccessSuperadmin(ValidateEndpointAccessBaseFixtures):
    """Tests for SUPERADMIN role access."""

    def test_superadmin_can_access_any_endpoint(
        self,
        base_validation_data: EndpointAccessValidationData,
        superadmin_requester_ctx: RequesterCtx,
    ) -> None:
        """SUPERADMIN should have access to any endpoint regardless of owner."""
        assert validate_endpoint_access(base_validation_data, superadmin_requester_ctx) is True

    def test_superadmin_can_access_superadmin_owned_endpoint(
        self,
        base_validation_data: EndpointAccessValidationData,
        superadmin_requester_ctx: RequesterCtx,
    ) -> None:
        """SUPERADMIN should access endpoints owned by other SUPERADMINs."""
        base_validation_data.session_owner_role = UserRole.SUPERADMIN

        assert validate_endpoint_access(base_validation_data, superadmin_requester_ctx) is True


class TestValidateEndpointAccessAdmin(ValidateEndpointAccessBaseFixtures):
    """Tests for ADMIN role access."""

    def test_admin_can_access_endpoint_in_same_domain(
        self,
        base_validation_data: EndpointAccessValidationData,
        admin_requester_ctx: RequesterCtx,
    ) -> None:
        """ADMIN should access endpoints in their domain owned by regular users."""
        base_validation_data.session_owner_role = UserRole.USER

        assert validate_endpoint_access(base_validation_data, admin_requester_ctx) is True

    def test_admin_cannot_access_endpoint_in_different_domain(
        self,
        base_validation_data: EndpointAccessValidationData,
        admin_requester_ctx: RequesterCtx,
    ) -> None:
        """ADMIN should NOT access endpoints in different domains."""
        base_validation_data.session_owner_role = UserRole.USER
        admin_requester_ctx.domain_name = "other-domain"

        assert validate_endpoint_access(base_validation_data, admin_requester_ctx) is False

    def test_admin_cannot_access_superadmin_owned_endpoint(
        self,
        base_validation_data: EndpointAccessValidationData,
        admin_requester_ctx: RequesterCtx,
    ) -> None:
        """ADMIN should NOT access endpoints owned by SUPERADMIN users.

        This is a critical security test - ADMIN users should never be able
        to access resources owned by SUPERADMIN users, even in the same domain.
        """
        base_validation_data.session_owner_role = UserRole.SUPERADMIN
        base_validation_data.domain = "test-domain"

        assert validate_endpoint_access(base_validation_data, admin_requester_ctx) is False

    def test_admin_can_access_admin_owned_endpoint_in_same_domain(
        self,
        base_validation_data: EndpointAccessValidationData,
        admin_requester_ctx: RequesterCtx,
    ) -> None:
        """ADMIN should access endpoints owned by other ADMINs in same domain."""
        base_validation_data.session_owner_role = UserRole.ADMIN

        assert validate_endpoint_access(base_validation_data, admin_requester_ctx) is True


class TestValidateEndpointAccessUser(ValidateEndpointAccessBaseFixtures):
    """Tests for regular USER role access."""

    def test_user_can_access_own_endpoint(
        self,
        base_validation_data: EndpointAccessValidationData,
        user_id: uuid.UUID,
        user_requester_ctx: RequesterCtx,
    ) -> None:
        """USER should access their own endpoints."""
        base_validation_data.session_owner_id = user_id

        assert validate_endpoint_access(base_validation_data, user_requester_ctx) is True

    def test_user_cannot_access_other_users_endpoint(
        self,
        base_validation_data: EndpointAccessValidationData,
        user_requester_ctx: RequesterCtx,
    ) -> None:
        """USER should NOT access other users' endpoints even in the same domain."""
        assert validate_endpoint_access(base_validation_data, user_requester_ctx) is False


class TestValidateEndpointAccessMonitor(ValidateEndpointAccessBaseFixtures):
    """Tests for MONITOR role access."""

    def test_monitor_can_access_own_endpoint(
        self,
        base_validation_data: EndpointAccessValidationData,
        user_id: uuid.UUID,
        monitor_requester_ctx: RequesterCtx,
    ) -> None:
        """MONITOR should access their own endpoints."""
        base_validation_data.session_owner_id = user_id

        assert validate_endpoint_access(base_validation_data, monitor_requester_ctx) is True

    def test_monitor_cannot_access_other_users_endpoint(
        self,
        base_validation_data: EndpointAccessValidationData,
        monitor_requester_ctx: RequesterCtx,
    ) -> None:
        """MONITOR should NOT access other users' endpoints."""
        assert validate_endpoint_access(base_validation_data, monitor_requester_ctx) is False


class TestValidateEndpointAccessEdgeCases(ValidateEndpointAccessBaseFixtures):
    """Tests for edge cases."""

    def test_endpoint_with_none_session_owner_role(
        self,
        base_validation_data: EndpointAccessValidationData,
        admin_requester_ctx: RequesterCtx,
    ) -> None:
        """ADMIN should access endpoints with None session_owner_role in same domain."""
        base_validation_data.session_owner_role = None

        # None != SUPERADMIN, so domain check applies
        assert validate_endpoint_access(base_validation_data, admin_requester_ctx) is True
