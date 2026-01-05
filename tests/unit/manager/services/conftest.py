"""
Shared fixtures for service unit tests.

Service tests should use mock repositories instead of real database connections.
This conftest provides guard fixtures to prevent accidental database usage.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def database_engine():
    """
    Guard fixture to prevent database usage in service tests.

    Service tests should use mock repositories instead of real database.
    If you need to test with a real database, use repository tests or component tests.
    """
    raise RuntimeError(
        "Service tests should not use database_engine. "
        "Use mock repositories instead. "
        "See: tests/unit/manager/services/conftest.py"
    )


@pytest.fixture
def database_fixture():
    """
    Guard fixture to prevent database fixture usage in service tests.

    Service tests should use mock repositories instead of real database fixtures.
    """
    raise RuntimeError(
        "Service tests should not use database_fixture. "
        "Use mock repositories instead. "
        "See: tests/unit/manager/services/conftest.py"
    )


@pytest.fixture
def database_connection():
    """
    Guard fixture to prevent database connection usage in service tests.

    Service tests should use mock repositories instead of real database connections.
    """
    raise RuntimeError(
        "Service tests should not use database_connection. "
        "Use mock repositories instead. "
        "See: tests/unit/manager/services/conftest.py"
    )
