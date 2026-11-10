from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.common.types import SessionTypes
from ai.backend.manager.errors.resource import (
    ResourceGroupNotFound,
    ResourceGroupSessionTypeNotAllowed,
)
from ai.backend.manager.registry import check_resource_group


def _create_mock_sgroup(name: str, allowed_session_types: list[str]) -> MagicMock:
    """Create a mock resource group carrying a name and its allowed session types."""
    mock = MagicMock()
    mock.name = name
    mock.scheduler.options.allowed_session_types = [
        SessionTypes(session_type) for session_type in allowed_session_types
    ]
    return mock


def test_allowed_session_types_check() -> None:
    candidates = [
        _create_mock_sgroup("a", ["batch"]),
        _create_mock_sgroup("b", ["interactive"]),
        _create_mock_sgroup("c", ["batch", "interactive"]),
    ]

    # Preferred scaling group with one match in allowed sgroups

    assert check_resource_group(candidates, "a", SessionTypes.BATCH) == "a"

    with pytest.raises(ResourceGroupSessionTypeNotAllowed) as e:
        check_resource_group(candidates, "b", SessionTypes.BATCH)
    assert "'b' does not accept" in str(e.value)

    assert check_resource_group(candidates, "c", SessionTypes.BATCH) == "c"

    with pytest.raises(ResourceGroupSessionTypeNotAllowed) as e:
        check_resource_group(candidates, "a", SessionTypes.INTERACTIVE)
    assert "'a' does not accept" in str(e.value)

    assert check_resource_group(candidates, "b", SessionTypes.INTERACTIVE) == "b"
    assert check_resource_group(candidates, "c", SessionTypes.INTERACTIVE) == "c"

    # Non-existent/disallowed preferred scaling group

    with pytest.raises(ResourceGroupNotFound) as exc_not_found:
        check_resource_group(candidates, "x", SessionTypes.INTERACTIVE)
    assert (
        "The scaling group 'x' does not exist "
        "or you do not have access to the scaling group 'x'." in str(exc_not_found.value)
    )

    # No preferred scaling group with partially matching allowed sgroups

    assert check_resource_group(candidates, None, SessionTypes.BATCH) == "a"
    assert check_resource_group(candidates, None, SessionTypes.INTERACTIVE) == "b"

    # No preferred scaling group with an empty list of allowed sgroups

    with pytest.raises(ResourceGroupNotFound) as exc_not_found_2:
        check_resource_group([], "x", SessionTypes.BATCH)
    assert "You have no scaling groups allowed to use." in str(exc_not_found_2.value)

    with pytest.raises(ResourceGroupNotFound) as exc_not_found_3:
        check_resource_group([], "x", SessionTypes.INTERACTIVE)
    assert "You have no scaling groups allowed to use." in str(exc_not_found_3.value)

    # No preferred scaling group with a non-empty list of allowed sgroups

    batch_only = [_create_mock_sgroup("a", ["batch"])]
    assert check_resource_group(batch_only, None, SessionTypes.BATCH) == "a"

    with pytest.raises(ResourceGroupNotFound) as exc_not_found_4:
        check_resource_group(batch_only, None, SessionTypes.INTERACTIVE)
    assert f"No scaling groups accept the session type '{SessionTypes.INTERACTIVE}'." in str(
        exc_not_found_4.value
    )
