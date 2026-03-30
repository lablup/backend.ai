from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import ErrorDetail, ErrorDomain, ErrorOperation
from ai.backend.common.health_checker import (
    HealthCheckerAlreadyRegistered,
    HealthCheckerNotFound,
)


def test_health_checker_already_registered_creation() -> None:
    """Test HealthCheckerAlreadyRegistered exception creation."""
    error = HealthCheckerAlreadyRegistered("Health checker already registered for manager/postgres")

    assert "manager/postgres" in str(error)
    assert error.status_code == 409  # HTTPConflict


def test_health_checker_already_registered_error_code() -> None:
    """Test HealthCheckerAlreadyRegistered error_code() returns correct values."""
    error = HealthCheckerAlreadyRegistered("Test message")
    error_code = error.error_code()

    assert error_code.domain == ErrorDomain.HEALTH_CHECK
    assert error_code.operation == ErrorOperation.CREATE
    assert error_code.error_detail == ErrorDetail.ALREADY_EXISTS


def test_health_checker_already_registered_inherits_http_conflict() -> None:
    """Test that HealthCheckerAlreadyRegistered inherits from web.HTTPConflict."""
    error = HealthCheckerAlreadyRegistered("Test message")
    assert isinstance(error, web.HTTPConflict)


def test_health_checker_not_found_creation() -> None:
    """Test HealthCheckerNotFound exception creation."""
    error = HealthCheckerNotFound("No health checker registered for agent/redis")

    assert "agent/redis" in str(error)
    assert error.status_code == 404  # HTTPNotFound


def test_health_checker_not_found_error_code() -> None:
    """Test HealthCheckerNotFound error_code() returns correct values."""
    error = HealthCheckerNotFound("Test message")
    error_code = error.error_code()

    assert error_code.domain == ErrorDomain.HEALTH_CHECK
    assert error_code.operation == ErrorOperation.READ
    assert error_code.error_detail == ErrorDetail.NOT_FOUND


def test_health_checker_not_found_inherits_http_not_found() -> None:
    """Test that HealthCheckerNotFound inherits from web.HTTPNotFound."""
    error = HealthCheckerNotFound("Test message")
    assert isinstance(error, web.HTTPNotFound)
