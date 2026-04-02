import json
import tempfile
from datetime import UTC, datetime

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.facts.server import Arch, Users, Which
from pyinfra.operations import files, server, systemd

from ai.backend.install.pyinfra.facts import FileContent
from ai.backend.install.pyinfra.os_packages import get_package_manager
from ai.backend.install.pyinfra.platform_utils import require_supported_platform
from ai.backend.install.pyinfra.runner import BaseDeploy
from ai.backend.install.pyinfra.utils import deep_merge


class DockerDeploy(BaseDeploy):
    # Docker Compose plugin installation paths (ordered by priority)
    DOCKER_COMPOSE_PLUGIN_PATHS = [
        "/usr/libexec/docker/cli-plugins/docker-compose",  # Official package location
        "/usr/local/lib/docker/cli-plugins/docker-compose",  # Custom binary location
        "/usr/lib/docker/cli-plugins/docker-compose",  # Alternative location
    ]

    # Custom Docker Compose installation paths
    CUSTOM_COMPOSE_DIR = "/usr/local/lib/docker/cli-plugins"
    CUSTOM_COMPOSE_BINARY = f"{CUSTOM_COMPOSE_DIR}/docker-compose"

    # Architecture mapping for Docker Compose binaries
    ARCH_MAP = {
        "x86_64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",  # macOS uses arm64
    }

    # Docker Compose offline repository path template (default)
    # Can be overridden via PYINFRA_DOCKER_COMPOSE_OFFLINE_PATH in .env
    DEFAULT_DOCKER_COMPOSE_OFFLINE_PATH = "custom/docker-compose-linux-{arch}"

    def __init__(self, host_data: object) -> None:
        self.user = host_data.bai_user
        self.bai_offline_repo_url = host_data.bai_offline_repo_url
        self.bai_offline_apt_url = host_data.bai_offline_apt_url
        self.agent = host_data.services.get("agent")

        # Initialize platform-appropriate package manager
        self.package_manager = get_package_manager(
            offline_repo_url=self.bai_offline_apt_url, fallback_repo_url=self.bai_offline_repo_url
        )

        self.packages = [
            "docker-ce",
            "docker-ce-cli",
            "containerd.io",
            "docker-buildx-plugin",
            "docker-compose-plugin",
            "docker-ce-rootless-extras",
        ]
        self.docker_installation_uri = host_data.docker_installation_uri
        self.docker_installation_os = host_data.docker_installation_os
        self.docker_installation_distro = host_data.docker_installation_distro
        self.docker_data_root = host_data.docker_data_root
        self.docker_default_address_pools = host_data.docker_default_address_pools
        self.docker_compose_offline_path = getattr(
            host_data, "docker_compose_offline_path", self.DEFAULT_DOCKER_COMPOSE_OFFLINE_PATH
        )

        self.container_registry_host = f"{host_data.registry_name}:{host_data.registry_port}"
        self.etc_docker_daemon_path = "/etc/docker/daemon.json"

    def install_docker_compose_from_custom(self) -> None:
        """
        Install Docker Compose plugin from custom offline repository.

        Downloads and installs the architecture-specific Docker Compose binary
        from the configured offline repository. Automatically detects system
        architecture and selects the appropriate binary.

        The binary is installed to /usr/local/lib/docker/cli-plugins/docker-compose
        which is one of the standard Docker plugin locations.

        Raises:
            SystemExit: If architecture is unsupported or download fails
        """
        # Get system architecture
        arch = host.get_fact(Arch)

        # Validate architecture support
        if arch not in self.ARCH_MAP:
            print(f"ERROR: Unsupported architecture for docker-compose: {arch}")
            print(f"Supported architectures: {', '.join(self.ARCH_MAP.keys())}")
            print("Please install Docker Compose manually or use a supported architecture.")
            raise SystemExit(f"Unsupported architecture: {arch}")

        compose_arch = self.ARCH_MAP[arch]
        compose_path = self.docker_compose_offline_path.format(arch=compose_arch)
        compose_url = f"{self.bai_offline_repo_url}/{compose_path}"

        print(f"Installing docker-compose for {arch} from custom repository...")
        print(f"Download URL: {compose_url}")

        # Create docker cli-plugins directory
        files.directory(
            name="Create docker cli-plugins directory",
            path=self.CUSTOM_COMPOSE_DIR,
            present=True,
            _sudo=True,
        )

        # Download docker-compose binary with error handling
        try:
            files.download(
                name=f"Download docker-compose from {compose_url}",
                src=compose_url,
                dest=self.CUSTOM_COMPOSE_BINARY,
                mode="755",
                _sudo=True,
            )
            print(f"Docker Compose installed successfully at: {self.CUSTOM_COMPOSE_BINARY}")
        except Exception as e:
            print(f"ERROR: Failed to download docker-compose from {compose_url}")
            print(f"Error details: {e}")
            print("\nPossible solutions:")
            print(f"1. Verify the file exists at: {compose_url}")
            print("2. Run gather_packages/collect_docker_compose.sh to collect the binary")
            print("3. Check network connectivity to the repository")
            print(f"4. Manually download and place the binary at: {self.CUSTOM_COMPOSE_BINARY}")
            raise

    def _check_docker_compose_installed(self) -> bool:
        """
        Check if Docker Compose plugin is already installed.

        Returns:
            True if Docker Compose is found in any of the standard plugin paths,
            False otherwise.
        """
        for path in self.DOCKER_COMPOSE_PLUGIN_PATHS:
            if host.get_fact(File, path=path):
                print(f"Docker Compose is already installed at: {path}")
                return True
        return False

    def install_docker(self) -> None:
        """
        Install Docker and Docker Compose.

        Checks if Docker is already installed. If present, verifies Docker Compose
        plugin availability and installs it from custom repository if missing.

        If Docker is not installed, installs it using one of three methods:
        1. Online installation from official Docker repository
        2. Offline installation from local package repository
        3. Direct installation from package files

        Also ensures Docker Compose plugin is available after installation.
        """
        # Check if Docker is already installed
        docker_path = host.get_fact(Which, command="docker")

        if docker_path:
            print(f"Docker is already installed at: {docker_path}")

            # Check if Docker Compose is already installed
            if not self._check_docker_compose_installed():
                print("Docker Compose not found. Installing from custom repository...")
                self.install_docker_compose_from_custom()

            print("Skipping Docker installation.")
            return

        print("Docker not found. Installing Docker packages...")

        protocol = "http"
        docker_domain = "download.docker.com"

        if self.docker_installation_uri.startswith(protocol):
            if docker_domain in self.docker_installation_uri:
                # Online installation mode - use unified package manager interface
                self.package_manager.setup_docker_repository(
                    self.docker_installation_uri,
                    self.docker_installation_os,
                    self.docker_installation_distro,
                    template_locator=self.locate_template,
                )
                self.package_manager.update_package_lists()
                self.package_manager.install_packages(self.packages)
            else:
                # Offline installation mode - use abstracted package manager
                with self.package_manager.offline_installation_context("docker-local-repo"):
                    self.package_manager.update_package_lists()
                    self.package_manager.install_packages(self.packages)
        else:
            # Direct package file installation mode
            platform_info = require_supported_platform("Docker direct installation")

            if platform_info.is_debian_based:
                # Direct DEB installation
                server.shell(
                    name="Install Docker through deb file",
                    commands=[f"cd {self.bai_offline_repo_url} && dpkg -i *.deb"],
                    _sudo=True,
                )
            elif platform_info.is_rhel_based:
                # Direct RPM installation
                server.shell(
                    name="Install Docker through rpm file",
                    commands=[f"cd {self.bai_offline_repo_url} && rpm -ivh *.rpm"],
                    _sudo=True,
                )
            else:
                raise ValueError(
                    f"Unsupported platform for Docker direct installation: {platform_info.platform_type.value}"
                )

    def apply_usermod(self) -> None:
        """
        Add the configured user to the docker group.

        This allows the user to run Docker commands without sudo.
        Only applies if the user exists on the system.
        """
        user_exists = self.user in host.get_fact(Users)
        if user_exists:
            server.shell(
                name=f"Add {self.user} to docker group",
                commands=[f"usermod -aG docker {self.user}"],
                _sudo=True,
            )

    def _build_daemon_json_config(self) -> dict:
        """
        Build Docker daemon.json configuration.

        Returns:
            Dictionary with Docker daemon configuration based on current settings.
        """
        accelerator_type = None
        if self.agent is not None:
            accelerator_type = self.agent.accelerator_type

        config = {
            "insecure-registries": [self.container_registry_host],
            "exec-opts": ["native.cgroupdriver=cgroupfs"],
            "storage-driver": "overlay2",
            "icc": False,
        }

        if self.docker_data_root:
            config["data-root"] = self.docker_data_root

        if accelerator_type == "cuda":
            config["runtimes"] = {
                "nvidia": {
                    "path": "nvidia-container-runtime",
                    "runtimeArgs": [],
                }
            }

        if self.docker_default_address_pools:
            config["default-address-pools"] = self.docker_default_address_pools

        return config

    def _backup_daemon_json(self) -> None:
        """Create a timestamped backup of the existing daemon.json file."""
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
        server.shell(
            name=f"Backup existing daemon.json ({timestamp})",
            commands=[
                f"cp -a {self.etc_docker_daemon_path} {self.etc_docker_daemon_path}.backup.{timestamp}"
            ],
            _sudo=True,
        )

    def make_etc_docker_daemon(self) -> None:
        """
        Create or update /etc/docker/daemon.json configuration file.

        This method intelligently merges new configuration with any existing
        daemon.json file on the remote host. It:
        1. Builds the required Docker daemon configuration
        2. Reads and parses any existing daemon.json file
        3. Deep-merges new settings with existing ones (preserving unrelated settings)
        4. Backs up the existing file before making changes
        5. Uploads the merged configuration
        6. Restarts the Docker service to apply changes

        If the configuration hasn't changed, skips the update to avoid
        unnecessary Docker service restarts.
        """
        # Build new configuration to merge
        new_config = self._build_daemon_json_config()

        # Check if daemon.json exists and read its content
        daemon_json_exists = host.get_fact(File, path=self.etc_docker_daemon_path)

        # Read existing daemon.json content from remote host using custom fact
        existing_config = {}
        if daemon_json_exists:
            daemon_json_content = host.get_fact(FileContent, path=self.etc_docker_daemon_path)

            if daemon_json_content and daemon_json_content.strip():
                try:
                    existing_config = json.loads(daemon_json_content)
                    print(f"Loaded existing daemon.json with keys: {list(existing_config.keys())}")
                except json.JSONDecodeError as e:
                    print(f"WARNING: Failed to parse daemon.json: {e}")
                    existing_config = {}
            else:
                print("daemon.json exists but is empty, starting with new config")

        # Merge new configuration with existing configuration
        merged_config = deep_merge(existing_config.copy(), new_config)

        # Check if configuration actually changed
        if existing_config and merged_config == existing_config:
            print("daemon.json already has the correct configuration, skipping update")
            return

        # Backup existing file before making changes
        if daemon_json_exists:
            self._backup_daemon_json()

        # Ensure all values are JSON serializable by round-trip conversion
        # Use default=str to convert non-serializable objects (like datetime) to strings
        try:
            json_string = json.dumps(merged_config, default=str, indent=4)
        except (TypeError, ValueError) as e:
            print(f"WARNING: Failed to serialize merged config, using new config only: {e}")
            json_string = json.dumps(new_config, default=str, indent=4)

        # Create temporary file with merged config
        # Note: Don't delete immediately - PyInfra operations run asynchronously
        # The OS will clean up /tmp periodically
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            tmp.write(json_string)
            tmp_path = tmp.name

        print("Updating daemon.json with new configuration...")

        # Ensure /etc/docker directory exists
        files.directory(
            name="Ensure /etc/docker directory exists",
            path="/etc/docker",
            present=True,
            _sudo=True,
        )

        # Upload merged configuration
        files.put(
            name="Upload merged daemon.json",
            src=tmp_path,
            dest=self.etc_docker_daemon_path,
            mode="644",
            _sudo=True,
        )

        # Restart Docker service
        systemd.service(
            name="Restart docker service",
            service="docker",
            running=True,
            restarted=True,
            enabled=True,
            _sudo=True,
        )

    def install(self) -> None:
        """
        Complete Docker installation workflow.

        Performs all necessary steps to set up Docker:
        1. Install Docker and Docker Compose
        2. Add configured user to docker group
        3. Create/update daemon.json configuration
        """
        self.install_docker()
        self.apply_usermod()
        self.make_etc_docker_daemon()

    def remove(self) -> None:
        """
        Complete Docker removal workflow.

        Performs comprehensive cleanup:
        1. Stops Docker and containerd services
        2. Removes custom Docker Compose installations
        3. Uninstalls Docker packages and repository configuration
        4. Removes Docker data directories (/var/lib/docker, /var/lib/containerd)
        5. Removes Docker configuration directory (/etc/docker)
        6. Removes user from docker group

        WARNING: This removes ALL Docker data including containers, images, and volumes.
        """
        print("WARNING: This will remove Docker and ALL container data!")
        print("Make sure to backup any important data before proceeding.")

        # Stop Docker service first
        systemd.service(
            name="Stop Docker service",
            service="docker",
            running=False,
            enabled=False,
            _sudo=True,
        )

        # Stop containerd service
        systemd.service(
            name="Stop containerd service",
            service="containerd",
            running=False,
            enabled=False,
            _sudo=True,
        )

        # Remove custom docker-compose installations
        files.file(
            name="Remove custom docker-compose binary",
            path=self.CUSTOM_COMPOSE_BINARY,
            present=False,
            _sudo=True,
        )
        files.directory(
            name="Remove custom docker-compose directory",
            path=self.CUSTOM_COMPOSE_DIR,
            present=False,
            _sudo=True,
        )

        # Use unified package manager interface for Docker removal
        self.package_manager.remove_docker_packages_and_repository(self.packages)

        # Remove Docker data directories (common to all platforms)
        for directory in ["/var/lib/docker", "/var/lib/containerd"]:
            files.directory(
                name=f"Remove Docker directory {directory}",
                path=directory,
                present=False,
                _sudo=True,
            )

        # Remove Docker configuration directory
        files.directory(
            name="Remove /etc/docker directory",
            path="/etc/docker",
            present=False,
            _sudo=True,
        )

        # Remove docker group from user if exists
        user_exists = self.user in host.get_fact(Users)
        if user_exists:
            server.shell(
                name=f"Remove {self.user} from docker group",
                commands=[f"gpasswd -d {self.user} docker 2>/dev/null || true"],
                _sudo=True,
            )

        print("Docker removal completed. System reboot recommended.")


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    DockerDeploy(host.data).run(deploy_mode)


main()
