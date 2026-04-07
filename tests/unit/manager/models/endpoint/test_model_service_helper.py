from __future__ import annotations

import uuid
from typing import Any
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


def _listdir_reply(filenames: list[str]) -> dict[str, Any]:
    return {"items": [{"name": name} for name in filenames]}


class TestValidateModelDefinitionFileExists:
    """Regression coverage for BA-5620.

    The non-custom runtime branch of `validate_model_service` calls this helper
    with `suggested_path=None` and relies on it accepting both
    `model-definition.yaml` and `model-definition.yml`.
    """

    async def test_resolves_yaml_when_only_yaml_present(self) -> None:
        storage_manager = _make_storage_manager()
        vfid = _make_vfid()

        with patch.object(
            ModelServiceHelper,
            "_listdir",
            new=AsyncMock(return_value=_listdir_reply(["model-definition.yaml", "weights.bin"])),
        ):
            result = await ModelServiceHelper.validate_model_definition_file_exists(
                storage_manager, "host", vfid, None
            )

        assert result == "model-definition.yaml"

    async def test_resolves_yml_when_only_yml_present(self) -> None:
        """BA-5620: a model storage with only `model-definition.yml` must be accepted."""
        storage_manager = _make_storage_manager()
        vfid = _make_vfid()

        with patch.object(
            ModelServiceHelper,
            "_listdir",
            new=AsyncMock(return_value=_listdir_reply(["model-definition.yml", "weights.bin"])),
        ):
            result = await ModelServiceHelper.validate_model_definition_file_exists(
                storage_manager, "host", vfid, None
            )

        assert result == "model-definition.yml"

    async def test_raises_when_neither_extension_present(self) -> None:
        storage_manager = _make_storage_manager()
        vfid = _make_vfid()

        with patch.object(
            ModelServiceHelper,
            "_listdir",
            new=AsyncMock(return_value=_listdir_reply(["README.md", "weights.bin"])),
        ):
            with pytest.raises(InvalidAPIParameters):
                await ModelServiceHelper.validate_model_definition_file_exists(
                    storage_manager, "host", vfid, None
                )

    async def test_suggested_path_must_match_exactly(self) -> None:
        storage_manager = _make_storage_manager()
        vfid = _make_vfid()

        with patch.object(
            ModelServiceHelper,
            "_listdir",
            new=AsyncMock(return_value=_listdir_reply(["custom-def.yaml"])),
        ):
            result = await ModelServiceHelper.validate_model_definition_file_exists(
                storage_manager, "host", vfid, "custom-def.yaml"
            )

        assert result == "custom-def.yaml"

    async def test_suggested_path_missing_raises(self) -> None:
        storage_manager = _make_storage_manager()
        vfid = _make_vfid()

        with patch.object(
            ModelServiceHelper,
            "_listdir",
            new=AsyncMock(return_value=_listdir_reply(["model-definition.yml"])),
        ):
            with pytest.raises(InvalidAPIParameters):
                await ModelServiceHelper.validate_model_definition_file_exists(
                    storage_manager, "host", vfid, "model-definition.yaml"
                )
