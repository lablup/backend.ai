from unittest.mock import AsyncMock

import pytest

from ai.backend.common.runner.types import Runner


@pytest.mark.asyncio
async def test_runner_setup():
    mock_resource = AsyncMock()
    runner = Runner([mock_resource])
    await runner.start()
    mock_resource.setup.assert_awaited_once()


@pytest.mark.asyncio
async def test_runner_close():
    mock_resource = AsyncMock()
    runner = Runner([mock_resource])
    await runner.start()
    await runner.close()
    mock_resource.release.assert_awaited_once()
