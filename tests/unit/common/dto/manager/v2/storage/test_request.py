"""Tests for ai.backend.common.dto.manager.v2.storage.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.v2.storage.request import (
    GetVFSStorageInput,
    ListVFSStorageInput,
    VFSDownloadFileInput,
    VFSListFilesInput,
)


class TestListVFSStorageInput:
    """Tests for ListVFSStorageInput model."""

    def test_default_values(self) -> None:
        req = ListVFSStorageInput()
        assert req.limit == DEFAULT_PAGE_LIMIT
        assert req.offset == 0

    def test_limit_default_equals_50(self) -> None:
        req = ListVFSStorageInput()
        assert req.limit == 50

    def test_limit_max_is_max_page_limit(self) -> None:
        req = ListVFSStorageInput(limit=MAX_PAGE_LIMIT)
        assert req.limit == MAX_PAGE_LIMIT

    def test_limit_exceeds_max_raises(self) -> None:
        with pytest.raises(ValidationError):
            ListVFSStorageInput(limit=MAX_PAGE_LIMIT + 1)

    def test_limit_below_1_raises(self) -> None:
        with pytest.raises(ValidationError):
            ListVFSStorageInput(limit=0)

    def test_negative_offset_raises(self) -> None:
        with pytest.raises(ValidationError):
            ListVFSStorageInput(offset=-1)

    def test_custom_limit_and_offset(self) -> None:
        req = ListVFSStorageInput(limit=10, offset=20)
        assert req.limit == 10
        assert req.offset == 20

    def test_round_trip(self) -> None:
        req = ListVFSStorageInput(limit=100, offset=50)
        restored = ListVFSStorageInput.model_validate_json(req.model_dump_json())
        assert restored.limit == 100
        assert restored.offset == 50


class TestGetVFSStorageInput:
    """Tests for GetVFSStorageInput model."""

    def test_valid_creation(self) -> None:
        req = GetVFSStorageInput(storage_name="nfs01")
        assert req.storage_name == "nfs01"

    def test_round_trip(self) -> None:
        req = GetVFSStorageInput(storage_name="cephfs")
        restored = GetVFSStorageInput.model_validate_json(req.model_dump_json())
        assert restored.storage_name == "cephfs"


class TestVFSDownloadFileInput:
    """Tests for VFSDownloadFileInput model."""

    def test_valid_creation(self) -> None:
        req = VFSDownloadFileInput(filepath="/data/file.bin")
        assert req.filepath == "/data/file.bin"

    def test_empty_filepath_raises(self) -> None:
        with pytest.raises(ValidationError):
            VFSDownloadFileInput(filepath="")

    def test_round_trip(self) -> None:
        req = VFSDownloadFileInput(filepath="/models/bert.onnx")
        restored = VFSDownloadFileInput.model_validate_json(req.model_dump_json())
        assert restored.filepath == "/models/bert.onnx"


class TestVFSListFilesInput:
    """Tests for VFSListFilesInput model."""

    def test_valid_creation(self) -> None:
        req = VFSListFilesInput(directory="/models")
        assert req.directory == "/models"

    def test_empty_directory_raises(self) -> None:
        with pytest.raises(ValidationError):
            VFSListFilesInput(directory="")

    def test_round_trip(self) -> None:
        req = VFSListFilesInput(directory="/data/checkpoints")
        restored = VFSListFilesInput.model_validate_json(req.model_dump_json())
        assert restored.directory == "/data/checkpoints"
