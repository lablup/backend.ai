from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.deployment.request import (
    ExtraVFolderMountInput,
    ModelMountConfigInput,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestModelMountConfigInput:
    def test_mount_destination_with_parent_segment_rejected(self) -> None:
        with pytest.raises(
            (BackendAISchemaValidationFailed, ValidationError),
            match=r"mount_destination must not contain a '\.\.' segment",
        ):
            ModelMountConfigInput.model_validate({
                "vfolder_id": str(uuid.uuid4()),
                "mount_destination": "/models/../models",
            })


class TestExtraVFolderMountInput:
    def test_null_mount_destination_accepted(self) -> None:
        mount = ExtraVFolderMountInput.model_validate({
            "vfolder_id": str(uuid.uuid4()),
            "mount_destination": None,
        })
        assert mount.mount_destination is None

    def test_mount_destination_with_parent_segment_rejected(self) -> None:
        with pytest.raises(
            (BackendAISchemaValidationFailed, ValidationError),
            match=r"mount_destination must not contain a '\.\.' segment",
        ):
            ExtraVFolderMountInput.model_validate({
                "vfolder_id": str(uuid.uuid4()),
                "mount_destination": "/home/work/../data",
            })
