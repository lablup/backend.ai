"""APT Repository Management Utility

This module provides APT repository management for Debian/Ubuntu systems.
"""

import logging
from typing import Any

from pyinfra.operations import apt, server

from .package_manager import PackageManager

logger = logging.getLogger(__name__)


class APTManager(PackageManager):
    """Manages APT repository configuration for various installation scenarios."""

    def __init__(
        self, offline_repo_url: str | None = None, fallback_repo_url: str | None = None
    ) -> None:
        """Initialize APT Manager.

        Args:
            offline_repo_url: URL for offline APT repository
            fallback_repo_url: Fallback repository URL if offline_repo_url is not specified
        """
        super().__init__(offline_repo_url, fallback_repo_url)

        # APT-specific backup paths
        self._sources_list_backup = f"/etc/apt/sources.list.{self._backup_suffix}"
        self._sources_list_d_backup = f"/etc/apt/sources.list.d.{self._backup_suffix}"

    def get_platform_name(self) -> str:
        """Return the platform name."""
        return "APT"

    def _acquire_lock(self) -> None:
        """Acquire a file lock to prevent concurrent APT modifications."""
        server.shell(
            name="Acquire APT manager lock",
            commands=[
                "mkdir -p /tmp",
                f"echo $$ > {self._lock_file}",
                "sleep 0.1",  # Small delay to reduce race conditions
            ],
            _sudo=False,
        )

    def _release_lock(self) -> None:
        """Release the file lock."""
        server.shell(
            name="Release APT manager lock",
            commands=[f"rm -f {self._lock_file}"],
            _sudo=False,
        )

    def backup_sources(self) -> None:
        """Backup original APT sources before modification with unique filenames."""
        if self._sources_backed_up:
            return

        self._acquire_lock()

        try:
            # Verify original files exist and create atomic backups
            server.shell(
                name=f"Backup original APT sources (suffix: {self._backup_suffix})",
                commands=[
                    # Verify source files exist before backup
                    "test -f /etc/apt/sources.list || touch /etc/apt/sources.list",
                    "test -d /etc/apt/sources.list.d || mkdir -p /etc/apt/sources.list.d",
                    # Create atomic backups with unique names
                    f"cp /etc/apt/sources.list {self._sources_list_backup}",
                    f"cp -r /etc/apt/sources.list.d {self._sources_list_d_backup}",
                    # Verify backup integrity
                    f"test -f {self._sources_list_backup}",
                    f"test -d {self._sources_list_d_backup}",
                    # Create verification marker
                    f"echo 'APT backup created at $(date)' > {self._sources_list_backup}.verify",
                ],
                _sudo=True,
            )
            self._sources_backed_up = True
            logger.info(f"APT sources backed up with suffix: {self._backup_suffix}")
        except Exception as e:
            logger.error(f"Failed to backup APT sources: {e}")
            self._release_lock()
            raise
        finally:
            self._release_lock()

    def restore_sources(self) -> None:
        """Restore original APT sources with atomic operations and verification."""
        if not self._sources_backed_up:
            logger.warning("No APT sources backup found, skipping restore")
            return

        self._acquire_lock()

        try:
            # Verify backup integrity before restore
            server.shell(
                name=f"Verify backup integrity before restore (suffix: {self._backup_suffix})",
                commands=[
                    f"test -f {self._sources_list_backup} || (echo 'Backup sources.list missing!' && exit 1)",
                    f"test -d {self._sources_list_d_backup} || (echo 'Backup sources.list.d missing!' && exit 1)",
                    f"test -f {self._sources_list_backup}.verify || (echo 'Backup verification marker missing!' && exit 1)",
                ],
                _sudo=True,
            )

            # Atomic restore operations using single script to maintain consistent PID
            restore_script = f"""
# Create temporary restore directory for atomic operations
TEMP_DIR="/tmp/apt-restore-$$"
mkdir -p "$TEMP_DIR"

# Prepare restore files
cp "{self._sources_list_backup}" "$TEMP_DIR/sources.list"
cp -r "{self._sources_list_d_backup}" "$TEMP_DIR/sources.list.d"

# Atomic replacement (as atomic as possible on filesystem level)
rm -rf /etc/apt/sources.list.d.old
mv /etc/apt/sources.list.d /etc/apt/sources.list.d.old || true
mv "$TEMP_DIR/sources.list.d" /etc/apt/sources.list.d
mv /etc/apt/sources.list /etc/apt/sources.list.old || true
mv "$TEMP_DIR/sources.list" /etc/apt/sources.list

# Cleanup old files and temp directory
rm -rf /etc/apt/sources.list.d.old /etc/apt/sources.list.old
rm -rf "$TEMP_DIR"

# Update APT cache
apt-get update || true
"""
            server.shell(
                name=f"Restore original APT sources (suffix: {self._backup_suffix})",
                commands=[restore_script],
                _sudo=True,
            )

            # Clean up backup files
            server.shell(
                name="Clean up APT backup files",
                commands=[
                    f"rm -rf {self._sources_list_backup}",
                    f"rm -rf {self._sources_list_d_backup}",
                    f"rm -f {self._sources_list_backup}.verify",
                    "rm -f /etc/apt/sources.list.disabled",
                    "rm -rf /etc/apt/sources.list.d.disabled",
                ],
                _sudo=True,
            )

            self._sources_backed_up = False
            logger.info(f"APT sources restored from backup with suffix: {self._backup_suffix}")

        except Exception as e:
            logger.error(f"Failed to restore APT sources: {e}")
            logger.error(
                "System may be in inconsistent state - manual intervention may be required"
            )
            raise
        finally:
            self._release_lock()

    def _cleanup_platform_specific_files(self) -> None:
        """Clean up APT-specific backup and temporary files."""
        server.shell(
            name="Clean up APT backup files",
            commands=[
                f"rm -rf {self._sources_list_backup}*",
                f"rm -rf {self._sources_list_d_backup}*",
                "rm -f /etc/apt/sources.list.disabled",
                "rm -rf /etc/apt/sources.list.d.disabled",
            ],
            _sudo=True,
        )

    def _emergency_restore_implementation(self) -> None:
        """Emergency APT sources restore - handles both backup files and .disabled files."""
        try:
            # Try multiple restoration strategies
            restoration_successful = False

            # Strategy 1: Use our backup files if they exist
            try:
                server.shell(
                    name="Check for our backup files",
                    commands=[
                        f"test -f /etc/apt/sources.list.{self._backup_suffix}",
                        f"test -d /etc/apt/sources.list.d.{self._backup_suffix}",
                    ],
                    _sudo=True,
                )

                # Force restoration from our backups
                self._sources_backed_up = True
                self.restore_sources()
                restoration_successful = True
                logger.info("Successfully restored from backup files")

            except Exception as backup_error:
                logger.warning(f"Could not restore from backup files: {backup_error}")

            # Strategy 2: Restore from .disabled files if backup failed
            if not restoration_successful:
                logger.info("Attempting to restore from .disabled files")
                server.shell(
                    name="Restore from .disabled files",
                    commands=[
                        # Check if .disabled files exist
                        "test -f /etc/apt/sources.list.disabled || echo 'No sources.list.disabled found'",
                        "test -d /etc/apt/sources.list.d.disabled || echo 'No sources.list.d.disabled found'",
                        # Restore from .disabled files
                        "if [ -f /etc/apt/sources.list.disabled ]; then mv /etc/apt/sources.list.disabled /etc/apt/sources.list; fi",
                        "if [ -d /etc/apt/sources.list.d.disabled ]; then rm -rf /etc/apt/sources.list.d; mv /etc/apt/sources.list.d.disabled /etc/apt/sources.list.d; fi",
                        # Update APT cache
                        "apt-get update || true",
                    ],
                    _sudo=True,
                )
                restoration_successful = True
                logger.info("Successfully restored from .disabled files")

            # Strategy 3: Look for any other backup files
            if not restoration_successful:
                logger.info("Searching for any available backup files")
                server.shell(
                    name="Search and restore from any backup",
                    commands=[
                        # Find and list any backup files
                        "find /etc/apt -name 'sources.list.bak-*' -o -name 'sources.list.*.orig' | head -1",
                        "find /etc/apt -name 'sources.list.d.bak-*' -type d | head -1",
                        # Try to restore from the most recent backup found
                        """
                        BACKUP_FILE=$(find /etc/apt -name 'sources.list.bak-*' -o -name 'sources.list.*.orig' | head -1)
                        BACKUP_DIR=$(find /etc/apt -name 'sources.list.d.bak-*' -type d | head -1)

                        if [ -n "$BACKUP_FILE" ]; then
                            echo "Restoring sources.list from $BACKUP_FILE"
                            cp "$BACKUP_FILE" /etc/apt/sources.list
                        fi

                        if [ -n "$BACKUP_DIR" ]; then
                            echo "Restoring sources.list.d from $BACKUP_DIR"
                            rm -rf /etc/apt/sources.list.d
                            cp -r "$BACKUP_DIR" /etc/apt/sources.list.d
                        fi

                        apt-get update || true
                        """,
                    ],
                    _sudo=True,
                )
                restoration_successful = True
                logger.info("Attempted restoration from found backup files")

        except Exception as e:
            logger.error(f"All emergency restore strategies failed: {e}")
            logger.error("Manual intervention required:")
            logger.error("1. Check /etc/apt/sources.list.bak-* and sources.list.*.orig files")
            logger.error("2. Check /etc/apt/sources.list.disabled file")
            logger.error("3. Check /etc/apt/sources.list.d.disabled/ directory")
            logger.error("4. Manually restore from any available backup")
            logger.error("5. Run 'apt-get update' to verify")
            raise

    def setup_offline_only_repositories(self, repo_filename: str = "local-repo-only") -> None:
        """Setup APT to use only the specified offline repository.

        Args:
            repo_filename: Name for the local repository file
        """
        repo_url = self.offline_repo_url or self.fallback_repo_url
        if not repo_url:
            raise ValueError("No offline APT URL or fallback repository URL specified")

        # Backup original sources
        self.backup_sources()

        # Disable all existing repositories by moving them
        server.shell(
            name="Disable existing APT repositories",
            commands=[
                "mkdir -p /etc/apt/sources.list.d.disabled",
                "mv /etc/apt/sources.list.d/* /etc/apt/sources.list.d.disabled/ || true",
                "mv /etc/apt/sources.list /etc/apt/sources.list.disabled || true",
                "touch /etc/apt/sources.list",
            ],
            _sudo=True,
        )

        # Add only the local repository
        apt.repo(
            name=f"Apply offline repository: {repo_url}",
            src=f"deb [trusted=yes] {repo_url} /",
            present=True,
            filename=repo_filename,
            _sudo=True,
        )
        logger.info(f"Offline-only APT repository configured: {repo_url}")

    def add_local_repository(self, repo_filename: str = "local-repo") -> None:
        """Add local repository alongside existing ones.

        Args:
            repo_filename: Name for the local repository file
        """
        repo_url = self.offline_repo_url or self.fallback_repo_url
        if not repo_url:
            raise ValueError("No offline APT URL or fallback repository URL specified")

        apt.repo(
            name=f"Add local repository: {repo_url}",
            src=f"deb [trusted=yes] {repo_url} /",
            present=True,
            filename=repo_filename,
            _sudo=True,
        )
        logger.info(f"Local APT repository added: {repo_url}")

    def update_package_lists(self) -> None:
        """Update APT package lists with guaranteed restoration on failure."""

        # Use a simpler approach that works with any shell
        restore_and_update_script = f"""
# Function to restore APT sources
restore_apt_sources() {{
    echo "=== RESTORING APT SOURCES ==="

    # Strategy 1: Restore from our backup files
    if [ -f "/etc/apt/sources.list.{self._backup_suffix}" ] && [ -d "/etc/apt/sources.list.d.{self._backup_suffix}" ]; then
        echo "Restoring from backup files (suffix: {self._backup_suffix})..."
        cp "/etc/apt/sources.list.{self._backup_suffix}" /etc/apt/sources.list
        rm -rf /etc/apt/sources.list.d
        cp -r "/etc/apt/sources.list.d.{self._backup_suffix}" /etc/apt/sources.list.d
        echo "Backup files restored"

    # Strategy 2: Restore from .disabled files
    elif [ -f "/etc/apt/sources.list.disabled" ] || [ -d "/etc/apt/sources.list.d.disabled" ]; then
        echo "Restoring from .disabled files..."
        [ -f "/etc/apt/sources.list.disabled" ] && mv /etc/apt/sources.list.disabled /etc/apt/sources.list
        if [ -d "/etc/apt/sources.list.d.disabled" ]; then
            rm -rf /etc/apt/sources.list.d
            mv /etc/apt/sources.list.d.disabled /etc/apt/sources.list.d
        fi
        echo "Disabled files restored"

    # Strategy 3: Look for any .orig files
    else
        echo "Looking for original backup files..."
        ORIG_FILE=$(find /etc/apt -name "sources.list.*.orig" | head -1)
        if [ -n "$ORIG_FILE" ]; then
            echo "Restoring from $ORIG_FILE"
            cp "$ORIG_FILE" /etc/apt/sources.list
        else
            echo "No backup files found!"
        fi
    fi

    echo "Updating APT cache after restoration..."
    apt-get update || true

    # Clean up backup files after successful restoration
    echo "Cleaning up backup files..."
    rm -f "/etc/apt/sources.list.{self._backup_suffix}"
    rm -f "/etc/apt/sources.list.{self._backup_suffix}.verify"
    rm -rf "/etc/apt/sources.list.d.{self._backup_suffix}"
    rm -f "/etc/apt/sources.list.disabled"
    rm -rf "/etc/apt/sources.list.d.disabled"

    echo "=== APT SOURCES RESTORATION COMPLETE ==="
}}

echo "Attempting APT update..."

# Try APT update and capture both exit code and output
apt-get update > /tmp/apt_update_output.log 2>&1
APT_EXIT_CODE=$?

# Check if update failed OR if critical errors occurred
if [ $APT_EXIT_CODE -ne 0 ] || grep -q "E: Failed to fetch" /tmp/apt_update_output.log; then
    echo "APT update failed or had critical errors - attempting restoration"
    cat /tmp/apt_update_output.log
    restore_apt_sources
    exit 1
else
    echo "APT update successful"
    cat /tmp/apt_update_output.log
fi

# Clean up
rm -f /tmp/apt_update_output.log
"""

        # Execute the update with guaranteed restoration on failure
        server.shell(
            name="Update APT repository with guaranteed restoration on failure",
            commands=[restore_and_update_script],
            _sudo=True,
        )

    def install_packages(self, packages: list[str], update: bool = False) -> None:
        """Install packages using APT with guaranteed restoration on failure.

        Args:
            packages: List of package names to install
            update: Whether to update package lists before installation
        """

        packages_str = " ".join(packages)
        update_flag = "--fix-missing" if update else ""

        # Create a shell script that handles both installation and restoration
        install_with_restore_script = f"""
# Function to restore APT sources
restore_apt_sources() {{
    echo "=== RESTORING APT SOURCES DUE TO INSTALLATION ERROR ==="

    # Strategy 1: Restore from our backup files
    if [ -f "/etc/apt/sources.list.{self._backup_suffix}" ] && [ -d "/etc/apt/sources.list.d.{self._backup_suffix}" ]; then
        echo "Restoring from backup files (suffix: {self._backup_suffix})..."
        cp "/etc/apt/sources.list.{self._backup_suffix}" /etc/apt/sources.list
        rm -rf /etc/apt/sources.list.d
        cp -r "/etc/apt/sources.list.d.{self._backup_suffix}" /etc/apt/sources.list.d
        echo "Backup files restored"

    # Strategy 2: Restore from .disabled files
    elif [ -f "/etc/apt/sources.list.disabled" ] || [ -d "/etc/apt/sources.list.d.disabled" ]; then
        echo "Restoring from .disabled files..."
        [ -f "/etc/apt/sources.list.disabled" ] && mv /etc/apt/sources.list.disabled /etc/apt/sources.list
        if [ -d "/etc/apt/sources.list.d.disabled" ]; then
            rm -rf /etc/apt/sources.list.d
            mv /etc/apt/sources.list.d.disabled /etc/apt/sources.list.d
        fi
        echo "Disabled files restored"
    fi

    echo "Updating APT cache after restoration..."
    apt-get update || true

    # Clean up backup files after successful restoration
    echo "Cleaning up backup files..."
    rm -f "/etc/apt/sources.list.{self._backup_suffix}"
    rm -f "/etc/apt/sources.list.{self._backup_suffix}.verify"
    rm -rf "/etc/apt/sources.list.d.{self._backup_suffix}"
    rm -f "/etc/apt/sources.list.disabled"
    rm -rf "/etc/apt/sources.list.d.disabled"

    echo "=== APT SOURCES RESTORATION COMPLETE ==="
}}

echo "Installing packages: {packages_str}"

# Try package installation
apt-get install -y {update_flag} {packages_str} > /tmp/apt_install_output.log 2>&1
INSTALL_EXIT_CODE=$?

# Check if installation failed
if [ $INSTALL_EXIT_CODE -ne 0 ]; then
    echo "Package installation failed - attempting restoration"
    cat /tmp/apt_install_output.log
    restore_apt_sources
    exit 1
else
    echo "Package installation successful"
    cat /tmp/apt_install_output.log
fi

# Clean up
rm -f /tmp/apt_install_output.log
"""

        # Execute the installation with guaranteed restoration on failure
        server.shell(
            name=f"Install packages with guaranteed restoration: {', '.join(packages)}",
            commands=[install_with_restore_script],
            _sudo=True,
        )
        logger.info(f"Installed packages: {', '.join(packages)}")

    def setup_docker_repository(
        self,
        docker_installation_uri: str,
        docker_installation_os: str,
        docker_installation_distro: str,
        template_locator: Any = None,
    ) -> None:
        """Setup Docker GPG key and repository for Debian/Ubuntu systems.

        Args:
            docker_installation_uri: Base URI for Docker installation
            docker_installation_os: OS identifier (e.g., 'ubuntu')
            docker_installation_distro: Distribution identifier (e.g., 'jammy')
            template_locator: Function to locate template files (optional, not used for APT)
        """
        from pyinfra.operations import apt, files, server

        # Install prerequisites
        apt.packages(
            name="Ensure APT deps. installed for Docker installation",
            packages=["ca-certificates", "curl"],
            latest=True,
            _sudo=True,
        )

        # Setup Docker GPG key
        files.directory(
            name="Create keyrings directory",
            path="/etc/apt/keyrings",
            present=True,
            _sudo=True,
        )
        files.download(
            name="Download Docker GPG key",
            src=f"{docker_installation_uri}/{docker_installation_os}/{docker_installation_distro}/gpg",
            dest="/etc/apt/keyrings/docker.asc",
            _sudo=True,
        )

        # Add Docker repository
        server.shell(
            name="Add Docker repository to Apt sources",
            commands=(
                'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] '
                f'{docker_installation_uri}/{docker_installation_os}/{docker_installation_distro} $(. /etc/os-release && echo "$VERSION_CODENAME") stable" '
                "| tee /etc/apt/sources.list.d/docker.list > /dev/null"
            ),
            _sudo=True,
        )

        logger.info(f"Docker repository configured: {docker_installation_uri}")

    def remove_docker_packages_and_repository(self, packages: list[str]) -> None:
        """Remove Docker packages and clean up repository configuration.

        Args:
            packages: List of Docker packages to remove
        """
        from pyinfra.operations import apt, files

        # Remove conflicting packages first (as per Docker official docs)
        conflicting_packages = [
            "docker.io",
            "docker-doc",
            "docker-compose",
            "docker-compose-v2",
            "podman-docker",
            "containerd",
            "runc",
        ]

        apt.packages(
            name="Remove conflicting Docker packages",
            packages=conflicting_packages,
            present=False,
            _sudo=True,
        )

        # Remove Docker CE packages that we installed
        apt.packages(
            name="Remove Docker CE packages",
            packages=packages,
            present=False,
            update=True,
            _sudo=True,
        )

        # Remove Docker GPG key and repository (if they exist)
        files.file(
            name="Remove Docker GPG key",
            path="/etc/apt/keyrings/docker.asc",
            present=False,
            _sudo=True,
        )

        files.file(
            name="Remove Docker APT repository",
            path="/etc/apt/sources.list.d/docker.list",
            present=False,
            _sudo=True,
        )

        logger.info("Docker packages and repository removed")
