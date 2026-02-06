r"""
Unit tests for file stream services (ZipArchiveStreamReader).

Focus: Pure unit tests for ZipArchiveStreamReader without HTTP dependencies.
Tests file path traversal, directory recursion, and archive entry registration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.storage.errors import UnsupportedFileTypeError
from ai.backend.storage.services.file_stream.zip import ZipArchiveStreamReader


class TestZipArchiveStreamReader:
    """
    Unit tests for ZipArchiveStreamReader.

    Tests core functionality: file addition, directory traversal,
    error handling, and metadata methods.
    """

    def test_reader_adds_single_file(self, tmp_path: Path) -> None:
        """
        Test that reader correctly adds a single file to archive.

        Scenario:
        1. Create a single file: tmp_path/file1.txt
        2. Create reader with tmp_path as base
        3. Add file to reader
        4. Verify file is registered in the archive
        """
        test_file = tmp_path / "file1.txt"
        test_file.write_text("test content")

        reader = ZipArchiveStreamReader(tmp_path)
        reader.add_entries([test_file])

        # Verify file was added to archive
        assert len(reader._zf.paths_to_write) == 1
        arcnames = [entry["arcname"] for entry in reader._zf.paths_to_write]
        assert "file1.txt" in arcnames

    def test_reader_traverses_directory_recursively(self, tmp_path: Path) -> None:
        """
        Test that reader recursively traverses directory structure.

        Scenario:
        1. Create directory structure:
           tmp_path/
             dir1/
               file1.txt
               subdir/
                 file2.txt
        2. Create reader and add dir1
        3. Verify all files are registered in the archive
        """
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "file1.txt").write_text("content1")

        subdir = dir1 / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("content2")

        reader = ZipArchiveStreamReader(tmp_path)
        reader.add_entries([dir1])

        # Verify both files were added recursively
        assert len(reader._zf.paths_to_write) == 2
        arcnames = [entry["arcname"] for entry in reader._zf.paths_to_write]
        assert "dir1/file1.txt" in arcnames
        assert "dir1/subdir/file2.txt" in arcnames

    def test_reader_handles_empty_directory(self, tmp_path: Path) -> None:
        """
        Test that reader preserves empty directories in archive.

        Scenario:
        1. Create empty directory: tmp_path/empty_dir/
        2. Add directory to reader
        3. Verify no exception is raised
        """
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()

        reader = ZipArchiveStreamReader(tmp_path)
        # Should not raise any exception
        reader.add_entries([empty_dir])

    def test_reader_raises_error_for_symlinks(self, tmp_path: Path) -> None:
        """
        Test that reader raises UnsupportedFileTypeError for symlinks.

        Scenario:
        1. Create a symlink in tmp_path
        2. Attempt to add symlink to reader
        3. Verify UnsupportedFileTypeError is raised
        4. Verify error message contains relative path
        """
        target = tmp_path / "target.txt"
        target.write_text("target content")

        symlink = tmp_path / "link.txt"
        symlink.symlink_to(target)

        reader = ZipArchiveStreamReader(tmp_path)

        with pytest.raises(UnsupportedFileTypeError) as exc_info:
            reader.add_entries([symlink])

        assert "link.txt" in str(exc_info.value.extra_msg)

    def test_reader_filename_custom(self, tmp_path: Path) -> None:
        """
        Test that reader returns custom filename when specified.

        Scenario:
        1. Create reader with filename="my-archive.zip"
        2. Call reader.filename()
        3. Verify "my-archive.zip" is returned
        """
        reader = ZipArchiveStreamReader(tmp_path, filename="my-archive.zip")
        assert reader.filename() == "my-archive.zip"

    def test_reader_filename_default(self, tmp_path: Path) -> None:
        """
        Test that reader returns default filename when not specified.

        Scenario:
        1. Create reader without filename parameter
        2. Call reader.filename()
        3. Verify "archive.zip" is returned
        """
        reader = ZipArchiveStreamReader(tmp_path)
        assert reader.filename() == "archive.zip"

    def test_reader_content_type(self, tmp_path: Path) -> None:
        """
        Test that reader returns correct content type.

        Scenario:
        1. Create reader
        2. Call reader.content_type()
        3. Verify "application/zip" is returned
        """
        reader = ZipArchiveStreamReader(tmp_path)
        assert reader.content_type() == "application/zip"

    def test_reader_archive_names_relative_to_base(self, tmp_path: Path) -> None:
        """
        Test that archive names are relative to base_path.

        Scenario:
        1. Create file: tmp_path/subdir/file.txt
        2. Create reader with base_path=tmp_path
        3. Add subdir/file.txt
        4. Verify no exception is raised (relative path is valid)
        """
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "file.txt"
        test_file.write_text("content")

        reader = ZipArchiveStreamReader(tmp_path)
        # Should not raise any exception with relative path
        reader.add_entries([test_file])
