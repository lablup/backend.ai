from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.storage.request import (
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
)


class TestGetPresignedUploadURL:
    async def test_presigned_upload_url_with_invalid_revision(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(Exception):
            await admin_registry.storage.get_presigned_upload_url(
                GetPresignedUploadURLReq(
                    artifact_revision_id=uuid.uuid4(),
                    key="test-file.txt",
                ),
            )


class TestGetPresignedDownloadURL:
    async def test_presigned_download_url_with_invalid_revision(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(Exception):
            await admin_registry.storage.get_presigned_download_url(
                GetPresignedDownloadURLReq(
                    artifact_revision_id=uuid.uuid4(),
                    key="test-file.txt",
                ),
            )
