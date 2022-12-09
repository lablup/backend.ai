import pytest

from ai.backend.client.session import Session

# module-level marker
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_list_agent():
    with Session() as sess:
        result = sess.Agent.list_with_limit(1, 0)
        assert len(result["items"]) == 1
