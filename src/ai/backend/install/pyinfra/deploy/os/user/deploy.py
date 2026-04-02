import re
from pathlib import Path
from typing import Any

from passlib.hash import sha512_crypt
from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDeploy


def hash_password(password: str) -> str:
    """Hash password using SHA-512 crypt for Linux /etc/shadow compatibility."""
    return sha512_crypt.hash(password)


def validate_ssh_public_key(key: str) -> bool:
    """Validate SSH public key format (ssh-rsa, ssh-ed25519, ecdsa-sha2-nistp*, ssh-dss)."""
    key = key.strip()
    if not key:
        return False

    ssh_key_pattern = re.compile(
        r"^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp(256|384|521)|ssh-dss)\s+[A-Za-z0-9+/]+[=]{0,3}(\s+.*)?$"
    )
    return bool(ssh_key_pattern.match(key))


class UserDeploy(BaseDeploy):
    """Deploy and manage Linux user account with SSH keys, group memberships, and optional passwordless sudo."""

    def __init__(self, host_data: Any) -> None:
        """Initialize with host configuration (user, UID/GID, password, SSH keys, groups)."""
        super().__init__()

        self.user: str = host_data.bai_user
        self.user_id: int = host_data.bai_user_id
        self.group_id: int = host_data.bai_user_group_id
        self.group: str = getattr(host_data, "bai_group", self.user)

        self.password: str = host_data.bai_user_password
        if not self.password or not self.password.strip():
            raise ValueError(f"Password is required and cannot be empty for user '{self.user}'")

        self.additional_groups: list[str] = getattr(
            host_data, "bai_user_groups", ["sudo", "docker"]
        )

        self.public_keys: list[str] | None = None
        if hasattr(host_data, "ssh_pubkey") and host_data.ssh_pubkey:
            self.public_keys = self._load_ssh_public_keys(host_data.ssh_pubkey)

        self.enable_passwordless_sudo: bool = getattr(host_data, "enable_passwordless_sudo", False)

    def _load_ssh_public_keys(self, ssh_pubkey: str) -> list[str]:
        """Load and validate SSH public keys from file path or raw string."""
        pubkey_path = Path(ssh_pubkey).expanduser()

        if pubkey_path.is_file():
            try:
                key_content = pubkey_path.read_text(encoding="utf-8")
                keys = [line.strip() for line in key_content.splitlines() if line.strip()]
            except PermissionError as e:
                raise PermissionError(
                    f"Cannot read SSH public key file '{pubkey_path}': {e}"
                ) from e
            except Exception as e:
                raise ValueError(f"Error reading SSH public key file '{pubkey_path}': {e}") from e
        else:
            keys = [ssh_pubkey.strip()]

        valid_keys = [key for key in keys if validate_ssh_public_key(key)]

        if not valid_keys:
            raise ValueError(
                "No valid SSH public keys found. "
                "Expected format: '<key-type> <base64-encoded-key> [comment]'"
            )

        return valid_keys

    def _configure_passwordless_sudo(self) -> None:
        """Configure passwordless sudo (creates /etc/sudoers.d/ file with 0440 permissions)."""
        sudoers_file = f"/etc/sudoers.d/90-{self.user}"
        sudoers_content = f"{self.user} ALL=(ALL) NOPASSWD: ALL"

        server.shell(
            name=f"Configure passwordless sudo for '{self.user}'",
            commands=[
                f"printf '{sudoers_content}\\n' | tee {sudoers_file} > /dev/null",
                f"chmod 440 {sudoers_file}",
                f"chown root:root {sudoers_file}",
            ],
            _sudo=True,
        )

        server.shell(
            name=f"Validate sudoers configuration for '{self.user}'",
            commands=[f"visudo -c -f {sudoers_file}"],
            _sudo=True,
        )

    def _remove_passwordless_sudo(self) -> None:
        """Remove passwordless sudo configuration file from /etc/sudoers.d/."""
        sudoers_file = f"/etc/sudoers.d/90-{self.user}"

        files.file(
            name=f"Remove passwordless sudo configuration for '{self.user}'",
            path=sudoers_file,
            present=False,
            _sudo=True,
        )

    def install(self) -> None:
        """Create group, user account with SSH keys and group memberships, and configure passwordless sudo if enabled."""
        hashed_password = hash_password(self.password)

        server.group(
            name=f"Create group '{self.group}' with GID={self.group_id}",
            group=self.group,
            present=True,
            gid=self.group_id,
            _sudo=True,
        )

        server.user(
            name=f"Create user '{self.user}' with UID:GID={self.user_id}:{self.group_id}",
            user=self.user,
            present=True,
            create_home=True,
            shell="/bin/bash",
            group=self.group,
            groups=self.additional_groups,
            public_keys=self.public_keys,
            uid=self.user_id,
            password=hashed_password,
            _sudo=True,
        )

        if self.enable_passwordless_sudo:
            self._configure_passwordless_sudo()

    def remove(self) -> None:
        """Remove passwordless sudo config, user account, and primary group (keeps home directory for safety)."""
        self._remove_passwordless_sudo()

        server.user(
            name=f"Remove user '{self.user}'",
            user=self.user,
            present=False,
            ensure_home=False,
            _sudo=True,
        )

        server.group(
            name=f"Remove group '{self.group}'",
            group=self.group,
            present=False,
            _sudo=True,
        )

    def update(self) -> None:
        """Update user configuration (idempotent - re-runs install to apply changes)."""
        self.install()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    UserDeploy(host.data).run(deploy_mode)


main()
