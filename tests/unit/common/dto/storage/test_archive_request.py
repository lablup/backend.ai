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

    @pytest.fixture
    def valid_body(self) -> dict[str, Any]:
        return {
            "volume": "vol1",
            "virtual_folder_id": str(VFolderID(None, uuid4())),
            "files": ["a.txt"],
        }

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            (None, None),
            ("export.zip", "export.zip"),
            ("데이터-export.zip", "데이터-export.zip"),
            ("report..final.zip", "report..final.zip"),
        ],
        ids=["omitted", "ascii", "unicode", "double_dots_in_name"],
    )
    def test_filename_accepted(
        self, valid_body: dict[str, Any], filename: str | None, expected: str | None
    ) -> None:
        req = CreateArchiveDownloadSessionRequest(**valid_body, filename=filename)
        assert req.filename == expected

    @pytest.mark.parametrize(
        "bad_filename",
        [
            "path/file.zip",
            "path\\file.zip",
            "..",
            ".",
            "foo\x00bar.zip",
            "foo\nbar.zip",
            "foo\rbar.zip",
            "",
            "   ",
        ],
        ids=[
            "slash",
            "backslash",
            "dotdot",
            "dot",
            "null_byte",
            "newline",
            "cr",
            "empty",
            "whitespace",
        ],
    )
    def test_filename_rejected(self, valid_body: dict[str, Any], bad_filename: str) -> None:
        with pytest.raises(ValidationError):
            CreateArchiveDownloadSessionRequest(**valid_body, filename=bad_filename)


class TestArchiveDownloadTokenDataFilename:
    """Verify filename field on ArchiveDownloadTokenData and JWT roundtrip."""

    @pytest.fixture
    def token_data_without_filename(self) -> ArchiveDownloadTokenData:
        return ArchiveDownloadTokenData(
            operation=TokenOperationType.DOWNLOAD,
            volume="vol1",
            virtual_folder_id=VFolderID(None, uuid4()),
            files=["a.txt"],
            exp=datetime.now(UTC) + timedelta(hours=1),
        )

    @pytest.fixture
    def token_data_with_filename(self) -> ArchiveDownloadTokenData:
        return ArchiveDownloadTokenData(
            operation=TokenOperationType.DOWNLOAD,
            volume="vol1",
            virtual_folder_id=VFolderID(None, uuid4()),
            files=["a.txt"],
            filename="custom.zip",
            exp=datetime.now(UTC) + timedelta(hours=1),
        )

    @pytest.fixture
    def token_data_with_unicode_filename(self) -> ArchiveDownloadTokenData:
        return ArchiveDownloadTokenData(
            operation=TokenOperationType.DOWNLOAD,
            volume="vol1",
            virtual_folder_id=VFolderID(None, uuid4()),
            files=["a.txt"],
            filename="데이터-export.zip",
            exp=datetime.now(UTC) + timedelta(hours=1),
        )

    def test_filename_defaults_to_none(
        self, token_data_without_filename: ArchiveDownloadTokenData
    ) -> None:
        assert token_data_without_filename.filename is None

    def test_filename_set(self, token_data_with_filename: ArchiveDownloadTokenData) -> None:
        assert token_data_with_filename.filename == "custom.zip"

    def test_jwt_roundtrip_preserves_filename(
        self, token_data_with_filename: ArchiveDownloadTokenData
    ) -> None:
        secret = "test-secret"
        payload = token_data_with_filename.model_dump(mode="json")
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["filename"] == "custom.zip"

    def test_jwt_roundtrip_filename_absent_or_null(
        self, token_data_without_filename: ArchiveDownloadTokenData
    ) -> None:
        secret = "test-secret"
        payload = token_data_without_filename.model_dump(mode="json")
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["filename"] is None

    def test_jwt_roundtrip_unicode_filename(
        self, token_data_with_unicode_filename: ArchiveDownloadTokenData
    ) -> None:
        secret = "test-secret"
        unicode_filename = "데이터-export.zip"
        payload = token_data_with_unicode_filename.model_dump(mode="json")
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded["filename"] == unicode_filename
