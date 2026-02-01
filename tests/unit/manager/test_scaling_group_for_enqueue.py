from __future__ import annotations

from unittest import mock
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from ai.backend.common.types import AccessKey, SessionTypes
from ai.backend.manager.errors.resource import (
    ScalingGroupNotFound,
    ScalingGroupSessionTypeNotAllowed,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.registry import check_scaling_group


def _create_mock_sgroup(name: str, allowed_session_types: list[str]) -> MagicMock:
    """Create a mock scaling group with proper attribute access."""
    mock = MagicMock()
    mock.name = name
    mock.scheduler_opts = ScalingGroupOpts.from_json({
        "allowed_session_types": allowed_session_types,
    })
    return mock


@pytest.mark.asyncio
@mock.patch("ai.backend.manager.registry.query_allowed_sgroups")
async def test_allowed_session_types_check(mock_query: MagicMock) -> None:
    mock_query.return_value = [
        _create_mock_sgroup("a", ["batch"]),
        _create_mock_sgroup("b", ["interactive"]),
        _create_mock_sgroup("c", ["batch", "interactive"]),
    ]
    mock_conn = MagicMock()
    mock_sess_ctx = MagicMock()

    # Test fixtures
    test_access_key = AccessKey("AKIAIOSFODNN7EXAMPLE")
    test_domain_name = "test-domain"
    test_group_id = UUID("12345678-1234-5678-1234-567812345678")

    # Preferred scaling group with one match in allowed sgroups

    session_type = SessionTypes.BATCH
    scaling_group = "a"
    result = await check_scaling_group(
        mock_conn, scaling_group, session_type, test_access_key, test_domain_name, test_group_id
    )
    assert result == scaling_group

    session_type = SessionTypes.BATCH
    scaling_group = "b"
    mock_sess_ctx.target_sgroup_names = []
    with pytest.raises(ScalingGroupSessionTypeNotAllowed) as e:
        result = await check_scaling_group(
            mock_conn, scaling_group, session_type, test_access_key, test_domain_name, test_group_id
        )
    assert f"'{scaling_group}' does not accept" in str(e.value)

    session_type = SessionTypes.BATCH
    scaling_group = "c"
    mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(
        mock_conn, scaling_group, session_type, test_access_key, test_domain_name, test_group_id
    )
    assert result == scaling_group

    session_type = SessionTypes.INTERACTIVE
    scaling_group = "a"
    mock_sess_ctx.target_sgroup_names = []
    with pytest.raises(ScalingGroupSessionTypeNotAllowed) as e:
        result = await check_scaling_group(
            mock_conn, scaling_group, session_type, test_access_key, test_domain_name, test_group_id
        )
    assert f"'{scaling_group}' does not accept" in str(e.value)

    session_type = SessionTypes.INTERACTIVE
    scaling_group = "b"
    mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(
        mock_conn, scaling_group, session_type, test_access_key, test_domain_name, test_group_id
    )
    assert result == scaling_group

    mock_sess_ctx.session_type = SessionTypes.INTERACTIVE
    mock_sess_ctx.scaling_group = "c"
    mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(
        mock_conn, scaling_group, session_type, test_access_key, test_domain_name, test_group_id
    )
    assert result == scaling_group

    # Non-existent/disallowed preferred scaling group

    session_type = SessionTypes.INTERACTIVE
    scaling_group = "x"
    mock_sess_ctx.target_sgroup_names = []
    with pytest.raises(ScalingGroupNotFound) as exc_not_found:
        result = await check_scaling_group(
            mock_conn, scaling_group, session_type, test_access_key, test_domain_name, test_group_id
        )
    assert (
        f"The scaling group '{scaling_group}' does not exist "
        f"or you do not have access to the scaling group '{scaling_group}'."
        in str(exc_not_found.value)
    )

    # No preferred scaling group with partially matching allowed sgroups

    session_type = SessionTypes.BATCH
    scaling_group_opt: str | None = None
    mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(
        mock_conn, scaling_group_opt, session_type, test_access_key, test_domain_name, test_group_id
    )
    assert result == "a"

    session_type = SessionTypes.INTERACTIVE
    scaling_group_opt = None
    mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(
        mock_conn, scaling_group_opt, session_type, test_access_key, test_domain_name, test_group_id
    )
    assert result == "b"

    # No preferred scaling group with an empty list of allowed sgroups

    mock_query.return_value = []

    session_type = SessionTypes.BATCH
    scaling_group = "x"
    mock_sess_ctx.target_sgroup_names = []
    with pytest.raises(ScalingGroupNotFound) as exc_not_found_2:
        result = await check_scaling_group(
            mock_conn, scaling_group, session_type, test_access_key, test_domain_name, test_group_id
        )
    assert "You have no scaling groups allowed to use." in str(exc_not_found_2.value)

    session_type = SessionTypes.INTERACTIVE
    scaling_group = "x"
    mock_sess_ctx.target_sgroup_names = []
    with pytest.raises(ScalingGroupNotFound) as exc_not_found_3:
        result = await check_scaling_group(
            mock_conn, scaling_group, session_type, test_access_key, test_domain_name, test_group_id
        )
    assert "You have no scaling groups allowed to use." in str(exc_not_found_3.value)

    # No preferred scaling group with a non-empty list of allowed sgroups

    mock_query.return_value = [
        _create_mock_sgroup("a", ["batch"]),
    ]

    session_type = SessionTypes.BATCH
    scaling_group_opt = None
    mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(
        mock_conn, scaling_group_opt, session_type, test_access_key, test_domain_name, test_group_id
    )
    assert result == "a"

    session_type = SessionTypes.INTERACTIVE
    scaling_group_opt = None
    mock_sess_ctx.target_sgroup_names = []
    with pytest.raises(ScalingGroupNotFound) as exc_not_found_4:
        result = await check_scaling_group(
            mock_conn,
            scaling_group_opt,
            session_type,
            test_access_key,
            test_domain_name,
            test_group_id,
        )
    assert f"No scaling groups accept the session type '{session_type}'." in str(
        exc_not_found_4.value
    )
