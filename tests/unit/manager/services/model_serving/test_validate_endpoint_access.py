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


@pytest.mark.parametrize(
    "requester_role, owner_role, requester_domain, endpoint_domain, is_owner, expected",
    [
        # SUPERADMIN: can access any endpoint regardless of owner or domain
        (UserRole.SUPERADMIN, UserRole.USER, "other-domain", "test-domain", False, True),
        (UserRole.SUPERADMIN, UserRole.SUPERADMIN, "other-domain", "test-domain", False, True),
        # ADMIN: can access same domain endpoints (except SUPERADMIN-owned)
        (UserRole.ADMIN, UserRole.USER, "test-domain", "test-domain", False, True),
        (UserRole.ADMIN, UserRole.USER, "other-domain", "test-domain", False, False),
        (UserRole.ADMIN, UserRole.SUPERADMIN, "test-domain", "test-domain", False, False),
        (UserRole.ADMIN, UserRole.ADMIN, "test-domain", "test-domain", False, True),
        # USER: can only access own endpoints
        (UserRole.USER, UserRole.USER, "test-domain", "test-domain", True, True),
        (UserRole.USER, UserRole.USER, "test-domain", "test-domain", False, False),
        # MONITOR: can only access own endpoints
        (UserRole.MONITOR, UserRole.USER, "test-domain", "test-domain", True, True),
        (UserRole.MONITOR, UserRole.USER, "test-domain", "test-domain", False, False),
        # Edge case: None owner role (ADMIN can access in same domain)
        (UserRole.ADMIN, None, "test-domain", "test-domain", False, True),
    ],
    ids=[
        "superadmin_can_access_any_endpoint",
        "superadmin_can_access_superadmin_owned",
        "admin_can_access_same_domain",
        "admin_cannot_access_different_domain",
        "admin_cannot_access_superadmin_owned",
        "admin_can_access_admin_owned_same_domain",
        "user_can_access_own_endpoint",
        "user_cannot_access_others_endpoint",
        "monitor_can_access_own_endpoint",
        "monitor_cannot_access_others_endpoint",
        "admin_can_access_none_owner_role",
    ],
)
def test_validate_endpoint_access(
    requester_role: UserRole,
    owner_role: UserRole | None,
    requester_domain: str,
    endpoint_domain: str,
    is_owner: bool,
    expected: bool,
) -> None:
    """Test access control logic for validate_endpoint_access function."""
    user_id = uuid.uuid4()
    owner_id = user_id if is_owner else uuid.uuid4()

    validation_data = EndpointAccessValidationData(
        session_owner_id=owner_id,
        session_owner_role=owner_role,
        domain=endpoint_domain,
    )

    requester_ctx = RequesterCtx(
        is_authorized=True,
        user_id=user_id,
        user_role=requester_role,
        domain_name=requester_domain,
    )

    assert validate_endpoint_access(validation_data, requester_ctx) == expected
