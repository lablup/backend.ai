"""Tests for archive download DTO models — filename field validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
import pytest
from pydantic import ValidationError

from ai.backend.common.dto.storage.request import (
    ArchiveDownloadTokenData,
    CreateArchiveDownloadSessionRequest,
    TokenOperationType,
)
from ai.backend.common.types import VFolderID


class TestCreateArchiveDownloadSessionRequestFilename:
    """Validate the filename field on CreateArchiveDownloadSessionRequest."""

    VALID_BODY: dict[str, Any] = {
        "volume": "vol1",
        "virtual_folder_id": str(VFolderID(None, uuid4())),
        "files": ["a.txt"],
    }

    def test_filename_omitted_defaults_to_none(self) -> None:
        req = CreateArchiveDownloadSessionRequest(**self.VALID_BODY)
        assert req.filename is None

    def test_filename_accepted_when_valid(self) -> None:
        req = CreateArchiveDownloadSessionRequest(**self.VALID_BODY, filename="export.zip")
        assert req.filename == "export.zip"

    def test_filename_unicode_accepted(self) -> None:
        req = CreateArchiveDownloadSessionRequest(**self.VALID_BODY, filename="데이터-export.zip")
        assert req.filename == "데이터-export.zip"

    @pytest.mark.parametrize(
        "bad_filename,reason",
        [
            ("path/file.zip", "contains /"),
            ("path\\file.zip", "contains \\"),
            ("..secret.zip", "contains .."),
            ("foo\x00bar.zip", "contains null byte"),
            ("", "empty string"),
            ("   ", "whitespace-only"),
        ],
        ids=["slash", "backslash", "dotdot", "null_byte", "empty", "whitespace"],
    )
    def test_filename_rejected_for_unsafe_values(self, bad_filename: str, reason: str) -> None:
        with pytest.raises(ValidationError):
            CreateArchiveDownloadSessionRequest(**self.VALID_BODY, filename=bad_filename)


class TestArchiveDownloadTokenDataFilename:
    """Verify filename field on ArchiveDownloadTokenData and JWT roundtrip."""

    def _make_token_data(self, filename: str | None = None) -> ArchiveDownloadTokenData:
        return ArchiveDownloadTokenData(
            operation=TokenOperationType.DOWNLOAD,
            volume="vol1",
            virtual_folder_id=VFolderID(None, uuid4()),
            files=["a.txt"],
            filename=filename,
            exp=datetime.now(UTC) + timedelta(hours=1),
        )

    def test_filename_defaults_to_none(self) -> None:
        data = self._make_token_data()
        assert data.filename is None

    def test_filename_set(self) -> None:
        data = self._make_token_data(filename="my-export.zip")
        assert data.filename == "my-export.zip"

    def test_jwt_roundtrip_preserves_filename(self) -> None:
        secret = "test-secret"
        data = self._make_token_data(filename="custom.zip")
        payload = data.model_dump(mode="json")
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["filename"] == "custom.zip"

    def test_jwt_roundtrip_without_filename(self) -> None:
        secret = "test-secret"
        data = self._make_token_data()
        payload = data.model_dump(mode="json")
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["filename"] is None

    def test_jwt_roundtrip_unicode_filename(self) -> None:
        secret = "test-secret"
        data = self._make_token_data(filename="데이터-export.zip")
        payload = data.model_dump(mode="json")
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["filename"] == "데이터-export.zip"
