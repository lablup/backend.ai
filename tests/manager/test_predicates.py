from __future__ import annotations

from unittest import mock
from unittest.mock import MagicMock

import pytest

from ai.backend.common.types import SessionTypes
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.scheduler.predicates import check_scaling_group


@pytest.mark.asyncio
@mock.patch('ai.backend.manager.scheduler.predicates.execute_with_retry')
async def test_allowed_session_types_check(mock_query):

    class DummyScalingGroup:
        def __init__(self, name, scheduler_opts) -> None:
            self.name = name
            self.scheduler_opts = scheduler_opts


    mock_query.return_value = [
        DummyScalingGroup(
            name='a',
            scheduler_opts=ScalingGroupOpts().from_json({
                'allowed_session_types': ['batch'],
            }),
        ),
        DummyScalingGroup(
            name='b',
            scheduler_opts=ScalingGroupOpts().from_json({
                'allowed_session_types': ['interactive'],
            }),
        ),
        DummyScalingGroup(
            name='c',
            scheduler_opts=ScalingGroupOpts().from_json({
                'allowed_session_types': ['batch', 'interactive'],
            }),
        ),
    ]
    mock_conn = MagicMock()
    mock_sched_ctx = MagicMock()
    mock_sess_ctx = MagicMock()

    # Preferred scaling group with one match in allowed sgroups

    mock_sess_ctx.session_type = SessionTypes.BATCH
    mock_sess_ctx.scaling_group_name = 'a'
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed
    # assert mock_sess_ctx.target_sgroup_names == ['a']

    mock_sess_ctx.session_type = SessionTypes.BATCH
    mock_sess_ctx.scaling_group_name = 'b'
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert not result.passed
    assert result.message is not None
    assert "does not accept" in result.message
    # assert mock_sess_ctx.target_sgroup_names == []

    mock_sess_ctx.session_type = SessionTypes.BATCH
    mock_sess_ctx.scaling_group_name = 'c'
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed
    # assert mock_sess_ctx.target_sgroup_names == ['c']

    mock_sess_ctx.session_type = SessionTypes.INTERACTIVE
    mock_sess_ctx.scaling_group_name = 'a'
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert not result.passed
    assert result.message is not None
    assert "does not accept" in result.message
    # assert mock_sess_ctx.target_sgroup_names == []

    mock_sess_ctx.session_type = SessionTypes.INTERACTIVE
    mock_sess_ctx.scaling_group_name = 'b'
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed
    # assert mock_sess_ctx.target_sgroup_names == ['b']

    mock_sess_ctx.session_type = SessionTypes.INTERACTIVE
    mock_sess_ctx.scaling_group_name = 'c'
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed
    # assert mock_sess_ctx.target_sgroup_names == ['c']

    # Non-existent/disallowed preferred scaling group

    mock_sess_ctx.session_type = SessionTypes.INTERACTIVE
    mock_sess_ctx.scaling_group_name = 'x'
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert not result.passed
    assert result.message is not None
    assert "do not have access" in result.message
    # assert mock_sess_ctx.target_sgroup_names == []

    # No preferred scaling group with partially matching allowed sgroups

    mock_sess_ctx.session_type = SessionTypes.BATCH
    mock_sess_ctx.scaling_group_name = None
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed
    # assert mock_sess_ctx.target_sgroup_names == ['a', 'c']

    mock_sess_ctx.session_type = SessionTypes.INTERACTIVE
    mock_sess_ctx.scaling_group_name = None
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed
    # assert mock_sess_ctx.target_sgroup_names == ['b', 'c']

    # No preferred scaling group with an empty list of allowed sgroups

    mock_query.return_value = []

    mock_sess_ctx.session_type = SessionTypes.BATCH
    mock_sess_ctx.scaling_group_name = 'x'
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert not result.passed
    assert result.message is not None
    assert "do not have any" in result.message
    # assert mock_sess_ctx.target_sgroup_names == []

    mock_sess_ctx.session_type = SessionTypes.INTERACTIVE
    mock_sess_ctx.scaling_group_name = 'x'
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert not result.passed
    assert result.message is not None
    assert "do not have any" in result.message
    # assert mock_sess_ctx.target_sgroup_names == []

    # No preferred scaling group with a non-empty list of allowed sgroups

    mock_query.return_value = [
        DummyScalingGroup(
            name='a',
            scheduler_opts=ScalingGroupOpts.from_json({
                'allowed_session_types': ['batch'],
            }),
        ),
    ]

    mock_sess_ctx.session_type = SessionTypes.BATCH
    mock_sess_ctx.scaling_group_name = None
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed
    # assert mock_sess_ctx.target_sgroup_names == ['a']

    mock_sess_ctx.session_type = SessionTypes.INTERACTIVE
    mock_sess_ctx.scaling_group_name = None
    # mock_sess_ctx.target_sgroup_names = []
    result = await check_scaling_group(mock_conn, mock_sched_ctx, mock_sess_ctx)
    assert not result.passed
    assert result.message is not None
    assert "No scaling groups accept" in result.message
    # assert mock_sess_ctx.target_sgroup_names == []
