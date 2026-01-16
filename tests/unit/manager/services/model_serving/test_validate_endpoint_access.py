"""
Unit tests for validate_endpoint_access function.

Tests verify access control logic for different user roles accessing endpoints.
"""

from __future__ import annotations

import uuid
from typing import NamedTuple

import pytest

from ai.backend.manager.data.model_serving.types import (
    EndpointAccessValidationData,
    RequesterCtx,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.services.utils import validate_endpoint_access


class EndpointAccessCase(NamedTuple):
    """Test case for endpoint access validation."""

    requester_role: UserRole
    owner_role: UserRole | None
    requester_domain: str
    endpoint_domain: str
    is_owner: bool
    expected: bool
    id: str


ENDPOINT_ACCESS_CASES = [
    # SUPERADMIN: can access any endpoint regardless of owner or domain
    EndpointAccessCase(
        requester_role=UserRole.SUPERADMIN,
        owner_role=UserRole.USER,
        requester_domain="other-domain",
        endpoint_domain="test-domain",
        is_owner=False,
        expected=True,
        id="superadmin_can_access_any_endpoint",
    ),
    EndpointAccessCase(
        requester_role=UserRole.SUPERADMIN,
        owner_role=UserRole.SUPERADMIN,
        requester_domain="other-domain",
        endpoint_domain="test-domain",
        is_owner=False,
        expected=True,
        id="superadmin_can_access_superadmin_owned",
    ),
    # ADMIN: can access same domain endpoints (except SUPERADMIN-owned)
    EndpointAccessCase(
        requester_role=UserRole.ADMIN,
        owner_role=UserRole.USER,
        requester_domain="test-domain",
        endpoint_domain="test-domain",
        is_owner=False,
        expected=True,
        id="admin_can_access_same_domain",
    ),
    EndpointAccessCase(
        requester_role=UserRole.ADMIN,
        owner_role=UserRole.USER,
        requester_domain="other-domain",
        endpoint_domain="test-domain",
        is_owner=False,
        expected=False,
        id="admin_cannot_access_different_domain",
    ),
    EndpointAccessCase(
        requester_role=UserRole.ADMIN,
        owner_role=UserRole.SUPERADMIN,
        requester_domain="test-domain",
        endpoint_domain="test-domain",
        is_owner=False,
        expected=False,
        id="admin_cannot_access_superadmin_owned",
    ),
    EndpointAccessCase(
        requester_role=UserRole.ADMIN,
        owner_role=UserRole.ADMIN,
        requester_domain="test-domain",
        endpoint_domain="test-domain",
        is_owner=False,
        expected=True,
        id="admin_can_access_admin_owned_same_domain",
    ),
    # USER: can only access own endpoints
    EndpointAccessCase(
        requester_role=UserRole.USER,
        owner_role=UserRole.USER,
        requester_domain="test-domain",
        endpoint_domain="test-domain",
        is_owner=True,
        expected=True,
        id="user_can_access_own_endpoint",
    ),
    EndpointAccessCase(
        requester_role=UserRole.USER,
        owner_role=UserRole.USER,
        requester_domain="test-domain",
        endpoint_domain="test-domain",
        is_owner=False,
        expected=False,
        id="user_cannot_access_others_endpoint",
    ),
    # MONITOR: can only access own endpoints
    EndpointAccessCase(
        requester_role=UserRole.MONITOR,
        owner_role=UserRole.USER,
        requester_domain="test-domain",
        endpoint_domain="test-domain",
        is_owner=True,
        expected=True,
        id="monitor_can_access_own_endpoint",
    ),
    EndpointAccessCase(
        requester_role=UserRole.MONITOR,
        owner_role=UserRole.USER,
        requester_domain="test-domain",
        endpoint_domain="test-domain",
        is_owner=False,
        expected=False,
        id="monitor_cannot_access_others_endpoint",
    ),
    # Edge case: None owner role (ADMIN can access in same domain)
    EndpointAccessCase(
        requester_role=UserRole.ADMIN,
        owner_role=None,
        requester_domain="test-domain",
        endpoint_domain="test-domain",
        is_owner=False,
        expected=True,
        id="admin_can_access_none_owner_role",
    ),
]


@pytest.mark.parametrize("case", ENDPOINT_ACCESS_CASES, ids=lambda c: c.id)
def test_validate_endpoint_access(case: EndpointAccessCase) -> None:
    """Test access control logic for validate_endpoint_access function."""
    user_id = uuid.uuid4()
    owner_id = user_id if case.is_owner else uuid.uuid4()

    validation_data = EndpointAccessValidationData(
        session_owner_id=owner_id,
        session_owner_role=case.owner_role,
        domain=case.endpoint_domain,
    )

    requester_ctx = RequesterCtx(
        is_authorized=True,
        user_id=user_id,
        user_role=case.requester_role,
        domain_name=case.requester_domain,
    )

    assert validate_endpoint_access(validation_data, requester_ctx) == case.expected
