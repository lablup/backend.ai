from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.types import AgentId, ImageID
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.services.image.actions.get_image_installed_agents import (
    GetImageInstalledAgentsAction,
    GetImageInstalledAgentsActionResult,
)


async def test_batch_load_installed_status_preserves_input_order() -> None:
    installed_image_id = ImageID(uuid.uuid4())
    uninstalled_image_id = ImageID(uuid.uuid4())
    processors = MagicMock()
    processors.image.get_image_installed_agents.wait_for_complete = AsyncMock(
        return_value=GetImageInstalledAgentsActionResult(
            data={installed_image_id: {AgentId("agent-001")}}
        )
    )
    adapter = ImageAdapter(processors)

    result = await adapter.batch_load_installed_status([
        uninstalled_image_id,
        installed_image_id,
    ])

    assert result == [False, True]
    processors.image.get_image_installed_agents.wait_for_complete.assert_awaited_once_with(
        GetImageInstalledAgentsAction(
            image_ids=[uninstalled_image_id, installed_image_id],
        )
    )
