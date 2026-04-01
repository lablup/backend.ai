r"""
Unit tests for file stream services (ZipArchiveStreamReader).

Focus: Pure unit tests for ZipArchiveStreamReader without HTTP dependencies.
Tests file path traversal, directory recursion, archive entry registration,
and actual ZIP stream read/download.
"""

from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path

import pytest

from ai.backend.storage.errors import UnsupportedFileTypeError
from ai.backend.storage.services.file_stream.zip import ZipArchiveStreamReader

OUTPUT_DIR = Path("/tmp/test-zip-output")


class TestZipArchiveStreamReader:
    """
    Unit tests for ZipArchiveStreamReader.

    Tests core functionality: file addition, directory traversal,
    error handling, metadata methods, and actual ZIP stream read/download.
    """

    # ── Fixtures ──

    @pytest.fixture(autouse=True)
    def _setup_output_dir(self) -> None:
        """Ensure OUTPUT_DIR exists. Cleans previous contents if present."""
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
        OUTPUT_DIR.mkdir(parents=True)

    @staticmethod
    async def _collect_and_save(reader: ZipArchiveStreamReader) -> bytes:
        """Consume the async iterator from read(), save to OUTPUT_DIR, and return bytes."""
        buf = io.BytesIO()
        async for chunk in reader.read():
            buf.write(chunk)
        data = buf.getvalue()
        (OUTPUT_DIR / reader.filename()).write_bytes(data)
        return data

    # ── add_entries tests ──

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

    # ── Metadata tests ──

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

    # ── read() / download stream tests ──

    async def test_read_single_file_produces_valid_zip(self, tmp_path: Path) -> None:
        """
        Test that read() produces a valid ZIP containing a single file.

        Scenario:
        1. Create tmp_path/hello.txt with known content
        2. Add it to the reader and call read()
        3. Verify the stream is a valid ZIP
        4. Verify the ZIP contains hello.txt with correct content
        """
        test_file = tmp_path / "hello.txt"
        test_file.write_text("hello world")

        reader = ZipArchiveStreamReader(tmp_path, filename="single_file.zip")
        reader.add_entries([test_file])

        data = await self._collect_and_save(reader)

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert zf.namelist() == ["hello.txt"]
            assert zf.read("hello.txt") == b"hello world"

    async def test_read_multiple_files(self, tmp_path: Path) -> None:
        """
        Test that read() produces a ZIP containing multiple files.

        Scenario:
        1. Create a.txt and b.txt with different content
        2. Add both to the reader and call read()
        3. Verify the ZIP contains both files with correct content
        """
        (tmp_path / "a.txt").write_text("aaa")
        (tmp_path / "b.txt").write_text("bbb")

        reader = ZipArchiveStreamReader(tmp_path, filename="multiple_files.zip")
        reader.add_entries([tmp_path / "a.txt", tmp_path / "b.txt"])

        data = await self._collect_and_save(reader)

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert sorted(zf.namelist()) == ["a.txt", "b.txt"]
            assert zf.read("a.txt") == b"aaa"
            assert zf.read("b.txt") == b"bbb"

    async def test_read_directory_with_nested_files(self, tmp_path: Path) -> None:
        """
        Test that read() correctly archives a directory tree.

        Scenario:
        1. Create directory structure:
           tmp_path/
             mydir/
               top.txt
               sub/
                 deep.txt
        2. Add mydir to the reader and call read()
        3. Verify ZIP contains both files with correct paths and content
        """
        mydir = tmp_path / "mydir"
        mydir.mkdir()
        (mydir / "top.txt").write_text("top")
        sub = mydir / "sub"
        sub.mkdir()
        (sub / "deep.txt").write_text("deep")

        reader = ZipArchiveStreamReader(tmp_path, filename="nested_dir.zip")
        reader.add_entries([mydir])

        data = await self._collect_and_save(reader)

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert sorted(zf.namelist()) == ["mydir/sub/deep.txt", "mydir/top.txt"]
            assert zf.read("mydir/top.txt") == b"top"
            assert zf.read("mydir/sub/deep.txt") == b"deep"

    async def test_read_mixed_files_and_directories(self, tmp_path: Path) -> None:
        """
        Test that read() handles a mix of individual files and directories.

        Scenario:
        1. Create a standalone file and a directory with files
        2. Add both to the reader and call read()
        3. Verify the ZIP contains all entries
        """
        standalone = tmp_path / "standalone.txt"
        standalone.write_text("solo")

        folder = tmp_path / "folder"
        folder.mkdir()
        (folder / "inside.txt").write_text("inner")

        reader = ZipArchiveStreamReader(tmp_path, filename="mixed.zip")
        reader.add_entries([standalone, folder])

        data = await self._collect_and_save(reader)

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert sorted(zf.namelist()) == ["folder/inside.txt", "standalone.txt"]
            assert zf.read("standalone.txt") == b"solo"
            assert zf.read("folder/inside.txt") == b"inner"

    async def test_read_large_file_streams_correctly(self, tmp_path: Path) -> None:
        """
        Test that read() handles a large file without corruption.

        Scenario:
        1. Create a file larger than the default inflight chunk queue (>8 chunks)
        2. Add it to the reader and call read()
        3. Verify the extracted content matches the original
        """
        large_content = b"x" * (1024 * 1024)  # 1 MB
        large_file = tmp_path / "large.bin"
        large_file.write_bytes(large_content)

        reader = ZipArchiveStreamReader(tmp_path, filename="large_file.zip")
        reader.add_entries([large_file])

        data = await self._collect_and_save(reader)

        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            assert zf.read("large.bin") == large_content
