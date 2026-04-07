from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderID
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.endpoint.row import ModelServiceHelper


def _make_storage_manager() -> MagicMock:
    storage_manager = MagicMock()
    storage_manager.get_proxy_and_volume = MagicMock(return_value=("proxy", "volume"))
    return storage_manager


def _make_vfid() -> VFolderID:
    return VFolderID(
        quota_scope_id=QuotaScopeID(QuotaScopeType.USER, uuid.uuid4()),
        folder_id=uuid.uuid4(),
    )


@pytest.mark.parametrize("filename", ["model-definition.yaml", "model-definition.yml"])
async def test_validate_model_definition_file_exists_accepts_both_extensions(
    filename: str,
) -> None:
    """BA-5620: helper must resolve both `.yaml` and `.yml` when no path is suggested."""
    with patch.object(
        ModelServiceHelper,
        "_listdir",
        new=AsyncMock(return_value={"items": [{"name": filename}]}),
    ):
        result = await ModelServiceHelper.validate_model_definition_file_exists(
            _make_storage_manager(), "host", _make_vfid(), None
        )

    assert result == filename


async def test_validate_model_definition_file_exists_raises_when_missing() -> None:
    """When neither extension is present and no path is suggested, the helper raises.

    The non-custom runtime branch in `validate_model_service` swallows this exception
    because the model definition file is optional for non-custom runtimes.
    """
    with patch.object(
        ModelServiceHelper,
        "_listdir",
        new=AsyncMock(return_value={"items": [{"name": "README.md"}]}),
    ):
        with pytest.raises(InvalidAPIParameters):
            await ModelServiceHelper.validate_model_definition_file_exists(
                _make_storage_manager(), "host", _make_vfid(), None
            )
