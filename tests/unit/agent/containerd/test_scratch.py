from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.containerd import scratch as scratch_module
from ai.backend.agent.containerd.scratch import (
    ScratchDirs,
    create_scratch,
    remove_scratch,
    write_config_files,
    write_dotfiles,
    write_hosts_file,
    write_resolv_conf,
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


class TestWriteResolvConf:
    @pytest.fixture
    def resolv(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
        host, systemd = tmp_path / "host-resolv.conf", tmp_path / "systemd-resolv.conf"
        monkeypatch.setattr(scratch_module, "_HOST_RESOLV_CONF", host)
        monkeypatch.setattr(scratch_module, "_SYSTEMD_RESOLV_CONF", systemd)
        return host, systemd

    def test_loopback_servers_are_dropped_and_search_options_kept(
        self, tmp_path: Path, resolv: tuple[Path, Path]
    ) -> None:
        host, _ = resolv
        host.write_text(
            "# c\nsearch example.com\nnameserver 127.0.0.53\nnameserver 10.0.0.2\n"
            "nameserver ::1\nnameserver fe80::1%eth0\noptions edns0\n"
        )
        dirs = _dirs(tmp_path)
        dirs.root.mkdir()

        write_resolv_conf(dirs)

        assert (
            dirs.resolv_conf.read_text()
            == "search example.com\nnameserver 10.0.0.2\noptions edns0\n"
        )

    def test_metadata_nameserver_is_dropped_and_warns_when_nothing_else_is_left(
        self, tmp_path: Path, resolv: tuple[Path, Path], mocker: MockerFixture
    ) -> None:
        host, _ = resolv
        host.write_text("nameserver 169.254.169.254\nsearch c.proj.internal\n")
        warning = mocker.patch.object(scratch_module.log, "warning")
        dirs = _dirs(tmp_path)
        dirs.root.mkdir()

        write_resolv_conf(dirs)

        assert dirs.resolv_conf.read_text() == "search c.proj.internal\n"
        warning.assert_called_once()

    def test_metadata_nameserver_is_dropped_next_to_a_usable_one(
        self, tmp_path: Path, resolv: tuple[Path, Path], mocker: MockerFixture
    ) -> None:
        host, _ = resolv
        host.write_text("nameserver 169.254.169.254\nnameserver 8.8.8.8\n")
        warning = mocker.patch.object(scratch_module.log, "warning")
        dirs = _dirs(tmp_path)
        dirs.root.mkdir()

        write_resolv_conf(dirs)

        assert dirs.resolv_conf.read_text() == "nameserver 8.8.8.8\n"
        warning.assert_not_called()

    def test_systemd_upstream_is_used_for_a_stub_only_host(
        self, tmp_path: Path, resolv: tuple[Path, Path]
    ) -> None:
        host, systemd = resolv
        host.write_text("nameserver 127.0.0.53\n")
        systemd.write_text("nameserver 192.168.0.1\nsearch lan\n")
        dirs = _dirs(tmp_path)
        dirs.root.mkdir()

        write_resolv_conf(dirs)

        assert dirs.resolv_conf.read_text() == "nameserver 192.168.0.1\nsearch lan\n"

    def test_no_usable_server_is_written_without_nameservers_and_warns(
        self, tmp_path: Path, resolv: tuple[Path, Path], mocker: MockerFixture
    ) -> None:
        host, _ = resolv
        host.write_text("nameserver 127.0.0.1\nsearch lan\n")
        warning = mocker.patch.object(scratch_module.log, "warning")
        dirs = _dirs(tmp_path)
        dirs.root.mkdir()

        write_resolv_conf(dirs)

        assert dirs.resolv_conf.read_text() == "search lan\n"
        warning.assert_called_once()

    def test_missing_host_file_is_tolerated(
        self, tmp_path: Path, resolv: tuple[Path, Path]
    ) -> None:
        dirs = _dirs(tmp_path)
        dirs.root.mkdir()

        write_resolv_conf(dirs)

        assert dirs.resolv_conf.read_text() == ""


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

    def test_absolute_path_outside_home_is_skipped(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)
        outside = tmp_path / "host" / "x"

        write_dotfiles(dirs, [{"path": str(outside), "data": "x", "perm": "644"}], None)

        assert not outside.exists()

    def test_home_path_escaping_the_scratch_root_is_skipped(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_dotfiles(dirs, [{"path": "/home/../../x", "data": "x", "perm": "644"}], None)

        assert not (tmp_path / "x").exists()
        assert not (tmp_path.parent / "x").exists()

    def test_relative_path_escaping_the_work_dir_is_skipped(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_dotfiles(dirs, [{"path": "../../x", "data": "x", "perm": "644"}], None)

        assert not (tmp_path / "x").exists()

    @pytest.mark.parametrize("path", [".", "", "/home/", "/home/work", ".config/.."])
    def test_a_path_naming_a_directory_is_skipped_not_fatal(
        self, tmp_path: Path, path: str
    ) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_dotfiles(dirs, [{"path": path, "data": "x", "perm": "644"}], None)

        assert dirs.work.is_dir()

    def test_a_skipped_dotfile_does_not_stop_the_others(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)

        write_dotfiles(
            dirs,
            [
                {"path": "/etc/x", "data": "bad", "perm": "644"},
                {"path": ".ok", "data": "ok", "perm": "644"},
            ],
            None,
        )

        assert (dirs.work / ".ok").read_text() == "ok\n"

    def test_chmod_walk_stops_at_the_work_dir(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)
        dirs.root.chmod(0o751)

        write_dotfiles(dirs, [{"path": "a/b/c", "data": "x", "perm": "600"}], None)

        assert oct((dirs.work / "a" / "b").stat().st_mode & 0o777) == "0o700"
        assert oct(dirs.work.stat().st_mode & 0o777) == "0o755"
        assert oct(dirs.root.stat().st_mode & 0o777) == "0o751"

    def test_chmod_walk_outside_the_work_dir_stops_at_the_scratch_root(
        self, tmp_path: Path
    ) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=False)
        dirs.root.parent.chmod(0o751)
        dirs.root.chmod(0o751)

        write_dotfiles(dirs, [{"path": "/home/config/sub/x", "data": "x", "perm": "600"}], None)

        assert (dirs.config / "sub" / "x").is_file()
        assert oct(dirs.root.parent.stat().st_mode & 0o777) == "0o751"
        assert oct(dirs.root.stat().st_mode & 0o777) == "0o751"


class TestRemoveScratch:
    def test_removes_the_kernel_dir(self, tmp_path: Path) -> None:
        dirs = _dirs(tmp_path)
        create_scratch(dirs, None, clone_dotfiles=True)

        remove_scratch(tmp_path, "k1")

        assert not dirs.root.exists()

    def test_missing_dir_is_tolerated(self, tmp_path: Path) -> None:
        remove_scratch(tmp_path, "absent")


class TestWriteHostsFile:
    @pytest.fixture
    def host_hosts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        path = tmp_path / "host-hosts"
        path.write_text("127.0.0.1 localhost")
        monkeypatch.setattr(scratch_module, "_HOST_HOSTS_FILE", path)
        return path

    def test_host_entries_and_the_kernel_hostname(self, tmp_path: Path, host_hosts: Path) -> None:
        dirs = _dirs(tmp_path / "s")
        dirs.root.mkdir(parents=True)

        write_hosts_file(dirs, "main1")

        assert dirs.hosts.read_text() == "127.0.0.1 localhost\n127.0.0.1 main1\n"
        assert dirs.hosts.stat().st_mode & 0o777 == 0o644
        assert dirs.hosts.parent == dirs.root

    def test_an_invalid_hostname_is_left_out(self, tmp_path: Path, host_hosts: Path) -> None:
        dirs = _dirs(tmp_path / "s")
        dirs.root.mkdir(parents=True)

        write_hosts_file(dirs, "bad name\n10.0.0.1 evil")

        assert dirs.hosts.read_text() == "127.0.0.1 localhost\n"

    def test_a_missing_host_file_gives_only_the_kernel_entry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(scratch_module, "_HOST_HOSTS_FILE", tmp_path / "absent")
        dirs = _dirs(tmp_path / "s")
        dirs.root.mkdir(parents=True)

        write_hosts_file(dirs, "main1")

        assert dirs.hosts.read_text() == "127.0.0.1 main1\n"
