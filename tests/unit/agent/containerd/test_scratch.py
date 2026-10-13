from __future__ import annotations

from pathlib import Path

from ai.backend.agent.containerd.scratch import (
    ScratchDirs,
    create_scratch,
    remove_scratch,
    write_config_files,
    write_dotfiles,
    write_intrinsic_ports,
)


def _dirs(tmp_path: Path) -> ScratchDirs:
    return ScratchDirs.for_kernel(tmp_path, "k1")


class TestScratchDirs:
    def test_layout(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)

        assert dirs.root == (tmp_path / "k1").resolve()
        assert dirs.config == dirs.root / "config"
        assert dirs.work == dirs.root / "work"

    def test_task_log_is_outside_the_mounted_dirs(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)

        assert dirs.task_log.parent == dirs.root


class TestCreateScratch:
    def test_creates_config_and_work_with_dotfiles(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)

        create_scratch(dirs, None, clone_dotfiles=True)

        assert dirs.config.is_dir()
        assert (dirs.work / ".bashrc").is_file()
        assert (dirs.work / "DO_NOT_STORE_PERSISTENT_FILES_HERE.md").is_file()
        assert (dirs.work / ".jupyter" / "custom" / "custom.css").is_file()
        assert oct(dirs.work.stat().st_mode & 0o777) == "0o755"

    def test_restart_keeps_the_work_dir_untouched(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)

        create_scratch(dirs, None, clone_dotfiles=False)

        assert list(dirs.work.iterdir()) == []

    def test_is_repeatable(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)

        create_scratch(dirs, None, clone_dotfiles=True)
        create_scratch(dirs, None, clone_dotfiles=True)

        assert (dirs.work / ".bashrc").is_file()


class TestWriteConfigFiles:
    def test_environ_resource_and_base_copies(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_config_files(
            dirs,
            environ="A=1\n",
            resource="CPU=1\n",
            bootstrap_script="echo hi",
            owner=None,
        )

        assert (dirs.config / "environ.txt").read_text() == "A=1\n"
        assert (dirs.config / "environ_base.txt").read_text() == "A=1\n"
        assert (dirs.config / "resource.txt").read_text() == "CPU=1\n"
        assert (dirs.config / "resource_base.txt").read_text() == "CPU=1\n"
        assert (dirs.work / "bootstrap.sh").read_text() == "echo hi"

    def test_no_bootstrap_script_no_file(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_config_files(dirs, environ="", resource="", bootstrap_script=None, owner=None)

        assert not (dirs.work / "bootstrap.sh").exists()

    def test_intrinsic_ports_are_written_for_the_kernel_runner(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_intrinsic_ports(dirs, b'{"replin": 30000, "replout": 30001}')

        assert (dirs.config / "intrinsic-ports.json").read_bytes() == (
            b'{"replin": 30000, "replout": 30001}'
        )


class TestWriteDotfiles:
    def test_relative_path_goes_to_the_work_dir(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_dotfiles(dirs, [{"path": ".config/app.conf", "data": "x=1", "perm": "644"}], None)

        target = dirs.work / ".config" / "app.conf"
        assert target.read_text() == "x=1\n"
        assert oct(target.stat().st_mode & 0o777) == "0o644"

    def test_home_path_is_mapped_into_the_scratch_root(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_dotfiles(dirs, [{"path": "/home/work/.zshrc", "data": "a\n", "perm": "600"}], None)

        assert (dirs.root / "work" / ".zshrc").read_text() == "a\n"

    def test_later_dotfile_overrides_the_earlier_one(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_dotfiles(
            dirs,
            [
                {"path": ".vimrc", "data": "first", "perm": "644"},
                {"path": ".vimrc", "data": "second", "perm": "644"},
            ],
            None,
        )

        assert (dirs.work / ".vimrc").read_text() == "second\n"


class TestRemoveScratch:
    def test_removes_the_kernel_dir(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=True)

        remove_scratch(tmp_path, "k1")

        assert not dirs.root.exists()

    def test_missing_dir_is_tolerated(self, tmp_path: Path) -> None:
        remove_scratch(tmp_path, "absent")
