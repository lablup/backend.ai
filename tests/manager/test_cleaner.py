from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.manager.cleaner import SessionCleaner
from ai.backend.manager.models.session import SessionStatus, SessionRow


@pytest.mark.asyncio
async def test_hanging_session_single_node_single_container(
    registry, stable_single_container_session
) -> None:
    session, kernel = stable_single_container_session
    assert session.created_at < datetime.now(tz=tzutc())

    await SessionCleaner(registry.db, registry).clean(
        status=SessionStatus.PENDING, threshold=timedelta(hours=1), interval=0
    )

    query = sa.select(SessionRow).where(SessionRow.id == session.id)
    async with registry.db.begin_readonly() as conn:
        result = await conn.execute(query)
        session = result.first()

    assert session.status == SessionStatus.CANCELLED
