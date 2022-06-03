import os
from pathlib import Path
import tempfile

from ai.backend.agent.docker.files import (
    scandir, diff_file_stats,
)


def test_scandir():
    # Create two files.
    with tempfile.TemporaryDirectory() as tmpdir:
        first = Path(tmpdir) / 'first.txt'
        first.write_text('first')
        second = Path(tmpdir) / 'second.txt'
        second.write_text('second')
        new_time = first.stat().st_mtime + 5
        os.utime(second, (new_time, new_time))

        file_stats = scandir(Path(tmpdir), 1000)

    assert len(file_stats) == 2
    assert int(file_stats[second]) == int(file_stats[first]) + 5


def test_scandir_skip_hidden_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        file = Path(tmpdir) / '.hidden_file'
        file.write_text('dark templar')
        file_stats = scandir(Path(tmpdir), 1000)

    assert len(file_stats) == 0


def test_scandir_skip_large_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        file = Path(tmpdir) / 'file.jpg'
        file.write_text('large file')
        file_stats = scandir(Path(tmpdir), 1)

    assert len(file_stats) == 0


def test_scandir_returns_files_in_sub_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        sub_folder = Path(tmpdir) / 'sub'
        sub_folder.mkdir()
        sub_file = sub_folder / 'sub-file.txt'
        sub_file.write_text('somedata')

        file_stats = scandir(Path(tmpdir), 1000)

    assert len(file_stats) == 1


def test_get_new_file_diff_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        first = Path(tmpdir) / 'first.txt'
        first.write_text('first')
        fs1 = scandir(tmpdir, 1000)

        second = Path(tmpdir) / 'second.txt'
        second.write_text('second')
        fs2 = scandir(tmpdir, 1000)

        diff_stats = diff_file_stats(fs1, fs2)

    assert first not in diff_stats
    assert second in diff_stats


def test_get_modified_file_diff_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        first = Path(tmpdir) / 'first.txt'
        first.write_text('first')
        second = Path(tmpdir) / 'second.txt'
        second.write_text('second')
        fs1 = scandir(tmpdir, 1000)

        new_time = first.stat().st_mtime + 5
        os.utime(second, (new_time, new_time))
        fs2 = scandir(tmpdir, 1000)

        diff_stats = diff_file_stats(fs1, fs2)

    assert first not in diff_stats
    assert second in diff_stats


def test_get_both_new_and_modified_files_stat():
    with tempfile.TemporaryDirectory() as tmpdir:
        first = Path(tmpdir) / 'first.txt'
        first.write_text('first')
        fs1 = scandir(tmpdir, 1000)

        new_time = first.stat().st_mtime + 5
        os.utime(first, (new_time, new_time))
        second = Path(tmpdir) / 'second.txt'
        second.write_text('second')
        fs2 = scandir(tmpdir, 1000)

        diff_stats = diff_file_stats(fs1, fs2)

    assert first in diff_stats
    assert second in diff_stats
