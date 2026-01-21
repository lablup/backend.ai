import pytest

from ai.backend.client.session import Session

# module-level marker
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_get_manager_status():
    with Session() as sess:
        resp = sess.Manager.status()
    assert resp["status"] == "running"
    assert "active_sessions" in resp
