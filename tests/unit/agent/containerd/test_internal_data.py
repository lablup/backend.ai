"""Provisioning of the manager-supplied ``internal_data`` into the kernel scratch.

The scratch dirs are bind-mounted as /home/work and /home/config, so everything here is plain
host-side file writing — no container access needed. The Docker backend has done this all along;
the containerd backend used to ignore internal_data entirely, which silently broke user SSH
login, dotfiles, the bootstrap script and registry credentials.
"""

import json
import os
from pathlib import Path
from typing import Any, cast

from ai.backend.agent.containerd.agent import ContainerdKernelCreationContext
from ai.backend.agent.resources import KernelResourceSpec, Mount
from ai.backend.common.types import MountPermission, MountTypes, ResourceSlot

_PUBKEY = "ssh-rsa AAAApublic user@host"
_PRIVKEY = "-----BEGIN OPENSSH PRIVATE KEY-----\nsecret\n-----END OPENSSH PRIVATE KEY-----"


def _context(
    scratch_dir: Path | None,
    *,
    internal_data: dict[str, Any] | None = None,
    bootstrap_script: str | None = None,
) -> ContainerdKernelCreationContext:
    ctx = ContainerdKernelCreationContext.__new__(ContainerdKernelCreationContext)
    ctx._scratch_dir = scratch_dir
    ctx.internal_data = internal_data or {}
    ctx.kernel_config = cast(Any, {"bootstrap_script": bootstrap_script})
    ctx.kernel_features = frozenset()
    return ctx


def _scratch(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    (base / "work").mkdir()
    (base / "config").mkdir()
    return base


def _spec(mounts: list[Mount] | None = None) -> KernelResourceSpec:
    return KernelResourceSpec(
        allocations={},
        slots=ResourceSlot(),
        mounts=mounts or [],
        scratch_disk_size=0,
    )


class TestSSHKeypair:
    async def test_writes_authorized_keys_and_id_container(self, tmp_path: Path) -> None:
        # Without authorized_keys the sshd service app rejects the user's key, so "SSH into my
        # session" — a first-class Backend.AI feature — simply does not work.
        scratch = _scratch(tmp_path)
        ctx = _context(
            scratch,
            internal_data={"ssh_keypair": {"public_key": _PUBKEY, "private_key": _PRIVKEY}},
        )
        await ctx._provision_internal_data(_spec())

        ssh_dir = scratch / "work" / ".ssh"
        assert (ssh_dir / "authorized_keys").read_text() == _PUBKEY
        assert (ssh_dir / "id_rsa").read_text() == _PRIVKEY
        assert (scratch / "work" / "id_container").read_text() == _PRIVKEY

    async def test_key_permissions_are_restrictive(self, tmp_path: Path) -> None:
        # sshd refuses to use a world-readable private key.
        scratch = _scratch(tmp_path)
        ctx = _context(
            scratch,
            internal_data={"ssh_keypair": {"public_key": _PUBKEY, "private_key": _PRIVKEY}},
        )
        await ctx._provision_internal_data(_spec())

        ssh_dir = scratch / "work" / ".ssh"
        assert ssh_dir.stat().st_mode & 0o777 == 0o700
        assert (ssh_dir / "authorized_keys").stat().st_mode & 0o777 == 0o600
        assert (ssh_dir / "id_rsa").stat().st_mode & 0o777 == 0o600
        assert (scratch / "work" / "id_container").stat().st_mode & 0o777 == 0o600

    async def test_user_mounted_ssh_vfolder_wins(self, tmp_path: Path) -> None:
        # The user mounted their own .ssh; overwriting it would clobber their keys.
        scratch = _scratch(tmp_path)
        ctx = _context(
            scratch,
            internal_data={"ssh_keypair": {"public_key": _PUBKEY, "private_key": _PRIVKEY}},
        )
        mounts = [
            Mount(
                MountTypes.BIND,
                Path("/vfroot/user-ssh"),
                Path("/home/work/.ssh"),
                MountPermission.READ_WRITE,
            )
        ]
        await ctx._provision_internal_data(_spec(mounts))

        assert not (scratch / "work" / ".ssh" / "authorized_keys").exists()

    async def test_existing_id_rsa_is_kept(self, tmp_path: Path) -> None:
        scratch = _scratch(tmp_path)
        ssh_dir = scratch / "work" / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_rsa").write_text("pre-existing")
        ctx = _context(
            scratch,
            internal_data={"ssh_keypair": {"public_key": _PUBKEY, "private_key": _PRIVKEY}},
        )
        await ctx._provision_internal_data(_spec())

        assert (ssh_dir / "id_rsa").read_text() == "pre-existing"


class TestBootstrapScript:
    async def test_written_to_work_dir(self, tmp_path: Path) -> None:
        scratch = _scratch(tmp_path)
        ctx = _context(scratch, bootstrap_script="#!/bin/sh\necho hello\n")
        await ctx._provision_internal_data(_spec())

        assert (scratch / "work" / "bootstrap.sh").read_text() == "#!/bin/sh\necho hello\n"

    async def test_absent_when_not_requested(self, tmp_path: Path) -> None:
        scratch = _scratch(tmp_path)
        ctx = _context(scratch)
        await ctx._provision_internal_data(_spec())

        assert not (scratch / "work" / "bootstrap.sh").exists()


class TestDockerCredentials:
    async def test_written_to_config_dir(self, tmp_path: Path) -> None:
        scratch = _scratch(tmp_path)
        creds = {"registry.example.com": {"username": "u", "password": "p"}}
        ctx = _context(scratch, internal_data={"docker_credentials": creds})
        await ctx._provision_internal_data(_spec())

        written = json.loads((scratch / "config" / "docker-creds.json").read_text())
        assert written == creds


class TestDotfiles:
    async def test_relative_path_lands_in_work_dir(self, tmp_path: Path) -> None:
        scratch = _scratch(tmp_path)
        ctx = _context(
            scratch,
            internal_data={"dotfiles": [{"path": ".bashrc", "data": "export A=1", "perm": "600"}]},
        )
        await ctx._provision_internal_data(_spec())

        target = scratch / "work" / ".bashrc"
        assert target.read_text() == "export A=1\n"  # trailing newline appended
        assert target.stat().st_mode & 0o777 == 0o600

    async def test_nested_path_is_created(self, tmp_path: Path) -> None:
        scratch = _scratch(tmp_path)
        ctx = _context(
            scratch,
            internal_data={
                "dotfiles": [{"path": ".config/nvim/init.vim", "data": "set nu", "perm": "644"}]
            },
        )
        await ctx._provision_internal_data(_spec())

        assert (scratch / "work" / ".config" / "nvim" / "init.vim").read_text() == "set nu\n"

    async def test_intermediate_dirs_stay_traversable(self, tmp_path: Path) -> None:
        # Applying the dotfile's own mode (e.g. 0644) to the directories leading to it would clear
        # their execute bit, so the container user could never traverse in and reach the file.
        scratch = _scratch(tmp_path)
        ctx = _context(
            scratch,
            internal_data={
                "dotfiles": [{"path": ".config/nvim/init.vim", "data": "set nu", "perm": "644"}]
            },
        )
        await ctx._provision_internal_data(_spec())

        work = scratch / "work"
        assert (work / ".config" / "nvim" / "init.vim").stat().st_mode & 0o777 == 0o644
        for d in (work / ".config", work / ".config" / "nvim"):
            assert d.stat().st_mode & 0o100, f"{d} is not traversable by its owner"

    async def test_a_relative_dotdot_path_is_refused(self, tmp_path: Path) -> None:
        # `../../evil` escapes the scratch; as root that is an arbitrary host write. The scratch is
        # a SUBdir of tmp_path so the escape target (a sibling of the scratch) is genuinely outside.
        scratch = _scratch(tmp_path / "scratch")
        escape_target = tmp_path / "evil-outside"
        rel = os.path.relpath(escape_target, scratch / "work")
        ctx = _context(
            scratch,
            internal_data={"dotfiles": [{"path": rel, "data": "PWNED", "perm": "600"}]},
        )
        await ctx._provision_internal_data(_spec())

        assert not escape_target.exists()  # the write outside the scratch never happened

    async def test_an_absolute_home_dotdot_path_is_refused(self, tmp_path: Path) -> None:
        # /home/work/../../evil also escapes once the /home prefix is stripped and joined.
        scratch = _scratch(tmp_path / "scratch")
        escape_target = tmp_path / "evil-outside"
        # after stripping the /home prefix, the path is joined under scratch; ../.. climbs out
        path = "/home/work/../../evil-outside"
        ctx = _context(
            scratch,
            internal_data={"dotfiles": [{"path": path, "data": "PWNED", "perm": "600"}]},
        )
        await ctx._provision_internal_data(_spec())

        assert not escape_target.exists()

    async def test_absolute_home_path_maps_into_the_scratch(self, tmp_path: Path) -> None:
        # /home/work/x and /home/config/x are this kernel's scratch dirs on the host.
        scratch = _scratch(tmp_path)
        ctx = _context(
            scratch,
            internal_data={
                "dotfiles": [{"path": "/home/work/.zshrc", "data": "setopt", "perm": "644"}]
            },
        )
        await ctx._provision_internal_data(_spec())

        assert (scratch / "work" / ".zshrc").read_text() == "setopt\n"

    async def test_absolute_non_home_path_is_skipped_not_written_to_the_host(
        self, tmp_path: Path
    ) -> None:
        # A path outside /home is in the image rootfs, unreachable from the host. It must never be
        # written to the agent's own filesystem.
        scratch = _scratch(tmp_path)
        victim = tmp_path / "etc-profile"
        ctx = _context(
            scratch,
            internal_data={"dotfiles": [{"path": str(victim), "data": "x", "perm": "644"}]},
        )
        await ctx._provision_internal_data(_spec())

        assert not victim.exists()

    async def test_later_dotfiles_overwrite_earlier_ones(self, tmp_path: Path) -> None:
        scratch = _scratch(tmp_path)
        ctx = _context(
            scratch,
            internal_data={
                "dotfiles": [
                    {"path": ".bashrc", "data": "low priority", "perm": "644"},
                    {"path": ".bashrc", "data": "high priority", "perm": "644"},
                ]
            },
        )
        await ctx._provision_internal_data(_spec())

        assert (scratch / "work" / ".bashrc").read_text() == "high priority\n"


class TestNoScratch:
    async def test_is_a_noop_without_a_scratch_dir(self) -> None:
        ctx = _context(
            None, internal_data={"dotfiles": [{"path": "x", "data": "y", "perm": "644"}]}
        )
        await ctx._provision_internal_data(_spec())  # must not raise
