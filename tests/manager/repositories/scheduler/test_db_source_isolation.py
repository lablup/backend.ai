"""
Test to verify that ScheduleDBSource uses READ COMMITTED isolation level.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource


@pytest.mark.asyncio
async def test_read_committed_isolation_level():
    """Test that all database operations use READ COMMITTED isolation level"""

    # Create a mock database engine
    mock_db = MagicMock()
    mock_conn = AsyncMock()
    mock_conn_with_options = AsyncMock()
    mock_transaction = AsyncMock()

    # Setup the mock chain - mock_db.connect() should return an async context manager
    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_connect_cm.__aexit__ = AsyncMock(return_value=None)
    mock_db.connect = MagicMock(return_value=mock_connect_cm)

    mock_conn.execution_options = AsyncMock(return_value=mock_conn_with_options)
    mock_conn_with_options.begin = MagicMock(return_value=mock_transaction)
    mock_transaction.__aenter__ = AsyncMock(return_value=None)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)

    # Create the ScheduleDBSource instance
    db_source = ScheduleDBSource(mock_db)

    # Test read-only session
    async with db_source._begin_readonly_session_read_committed():
        pass

    # Verify that execution_options was called with READ COMMITTED and postgresql_readonly
    mock_conn.execution_options.assert_called_with(
        isolation_level="READ COMMITTED",
        postgresql_readonly=True,
    )

    # Reset mock for next test
    mock_conn.execution_options.reset_mock()

    # Test read-write session
    async with db_source._begin_session_read_committed():
        pass

    # Verify that execution_options was called with READ COMMITTED
    mock_conn.execution_options.assert_called_with(isolation_level="READ COMMITTED")

    # Reset mock for next test
    mock_conn.execution_options.reset_mock()

    # Test read-only connection
    async with db_source._begin_readonly_read_committed():
        pass

    # Verify that execution_options was called with READ COMMITTED and postgresql_readonly
    mock_conn.execution_options.assert_called_with(
        isolation_level="READ COMMITTED",
        postgresql_readonly=True,
    )


@pytest.mark.asyncio
async def test_session_methods_use_read_committed():
    """Test that public methods use the READ COMMITTED session methods"""

    # Create a mock database engine and ScheduleDBSource
    mock_db = MagicMock()
    db_source = ScheduleDBSource(mock_db)

    # Mock the internal session methods
    db_source._begin_readonly_session_read_committed = AsyncMock()
    db_source._begin_session_read_committed = AsyncMock()
    db_source._begin_readonly_read_committed = AsyncMock()

    # Create mock session context managers
    mock_readonly_session = AsyncMock()
    mock_readonly_session.__aenter__ = AsyncMock(return_value=mock_readonly_session)
    mock_readonly_session.__aexit__ = AsyncMock(return_value=None)

    mock_write_session = AsyncMock()
    mock_write_session.__aenter__ = AsyncMock(return_value=mock_write_session)
    mock_write_session.__aexit__ = AsyncMock(return_value=None)

    mock_readonly_conn = AsyncMock()
    mock_readonly_conn.__aenter__ = AsyncMock(return_value=mock_readonly_conn)
    mock_readonly_conn.__aexit__ = AsyncMock(return_value=None)

    db_source._begin_readonly_session_read_committed.return_value = mock_readonly_session
    db_source._begin_session_read_committed.return_value = mock_write_session
    db_source._begin_readonly_read_committed.return_value = mock_readonly_conn

    # Test get_scheduling_data (uses readonly session)
    mock_readonly_session.execute = AsyncMock(return_value=MagicMock())

    try:
        await db_source.get_scheduling_data("test-scaling-group", MagicMock())
    except Exception:
        # We expect it to fail due to mocking, but we just want to verify the method was called
        pass

    # Verify that the READ COMMITTED session method was called
    assert db_source._begin_readonly_session_read_committed.called
