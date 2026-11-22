from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from ai.backend.common.dotfile import DotfilePath, InvalidDotfilePath, validate_dotfile_perm


@pytest.mark.parametrize(
    ("raw", "relative"),
    [
        (".bashrc", ".bashrc"),
        (".zshrc", ".zshrc"),
        (".tmux.conf.local", ".tmux.conf.local"),
        (".vimrc", ".vimrc"),
        (".Renviron", ".Renviron"),
        (".aws/config", ".aws/config"),
        (".ssh/config", ".ssh/config"),
        (".ssh/id_rsa", ".ssh/id_rsa"),
        (".app/cluster.json", ".app/cluster.json"),
        ("notes.txt", "notes.txt"),
        ("./.bashrc", ".bashrc"),
        ("/home/work/.bashrc", ".bashrc"),
        ("/home/work/.aws/config", ".aws/config"),
    ],
)
def test_accepts_paths_under_work_dir(raw: str, relative: str) -> None:
    assert DotfilePath(raw).relative == PurePosixPath(relative)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        ".",
        "/",
        "/home/work",
        "/home/work/",
        "/etc/passwd",
        "/home",
        "/home/config/kconfig.dat",
        "/home/other/.bashrc",
        "/home/workspace/.bashrc",
        "//home/work/.bashrc",
        "..",
        "../config/kconfig.dat",
        ".a/../.bashrc",
        "/home/work/../config/kconfig.dat",
        ".a\x00b",
    ],
)
def test_rejects_paths_outside_work_dir(raw: str) -> None:
    with pytest.raises(InvalidDotfilePath):
        DotfilePath(raw)


@pytest.mark.parametrize(
    "raw",
    [
        ".terminfo",
        ".jupyter",
        ".ssh",
        ".ssh/",
        ".ssh/authorized_keys",
        ".ssh//authorized_keys",
        "./.ssh/authorized_keys",
        ".local",
        ".config",
        "/home/work/.ssh/authorized_keys",
        "config",
        "config/kconfig.dat",
        "ssh/id_cluster",
        "restart-state/kconfig.dat",
        "kconfig.dat",
        "cluster.json",
        "environ.txt",
        "environ_base.txt",
        "resource.txt",
        "resource_base.txt",
        "docker-creds.json",
        "intrinsic-ports.json",
        "dotfiles.json",
        "id_container",
        "/home/work/kconfig.dat",
    ],
)
def test_rejects_reserved_names(raw: str) -> None:
    with pytest.raises(InvalidDotfilePath):
        DotfilePath(raw)


@pytest.mark.parametrize(
    "raw",
    [
        ".bashrc\n",
        ".a\nwork f0 0755 .bashrc",
        ".a\rb",
        ".a\tb",
        ".a\x1bb",
        ".a\x7fb",
        ".a\x85b",
        " .bashrc",
        ".bashrc ",
    ],
)
def test_rejects_control_characters_and_outer_whitespace(raw: str) -> None:
    with pytest.raises(InvalidDotfilePath):
        DotfilePath(raw)


@pytest.mark.parametrize("raw", ["644", "0644", "0755", "000", "0777", "600"])
def test_accepts_octal_modes(raw: str) -> None:
    assert validate_dotfile_perm(raw) == raw


@pytest.mark.parametrize(
    "raw", ["", "64", "1777", "04755", "0o644", "0844", "rwx", "0644\n", " 644", "-1"]
)
def test_rejects_other_modes(raw: str) -> None:
    with pytest.raises(InvalidDotfilePath):
        validate_dotfile_perm(raw)
