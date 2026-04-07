from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderID
from ai.backend.manager.models.endpoint.row import ModelServiceHelper


@pytest.mark.parametrize("filename", ["model-definition.yaml", "model-definition.yml"])
async def test_validate_model_definition_file_exists_accepts_both_extensions(
    filename: str,
) -> None:
    """BA-5620: helper must resolve both `.yaml` and `.yml` when no path is suggested."""
    storage_manager = MagicMock()
    storage_manager.get_proxy_and_volume = MagicMock(return_value=("proxy", "volume"))
    vfid = VFolderID(
        quota_scope_id=QuotaScopeID(QuotaScopeType.USER, uuid.uuid4()),
        folder_id=uuid.uuid4(),
    )

    with patch.object(
        ModelServiceHelper,
        "_listdir",
        new=AsyncMock(return_value={"items": [{"name": filename}]}),
    ):
        result = await ModelServiceHelper.validate_model_definition_file_exists(
            storage_manager, "host", vfid, None
        )

    assert result == filename
