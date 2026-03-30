import inspect
import os
from enum import Enum
from pathlib import Path
from typing import Any

from pyinfra import host as current_host
from pyinfra import logger
from pyinfra.operations import files, pip, server, systemd

from ai.backend.install.pyinfra.docker import get_docker_compose_cmd
from ai.backend.install.pyinfra.exceptions import ConfigurationError, MissingAttributeError
from ai.backend.install.pyinfra.utils import load_container_image


class DeployMode(Enum):
    INSTALL = "install"
    REMOVE = "remove"
    UPDATE = "update"


def _create_management_scripts(
    deploy_instance: "BaseDeploy",
    service_dir: Path | str,
    template_dir: str = "docker",
    extra_context: dict[str, Any] | None = None,
) -> None:
    """
    Create standard management scripts (start/stop/logs/status) for a service.

    This is a utility function used by BaseDeploy.create_service_manage_scripts()
    template method. Deploy scripts should not call this directly - use the
    template method or hook methods instead.

    Args:
        deploy_instance: BaseDeploy instance (needed for locate_template)
        service_dir: Service directory where scripts will be created
        template_dir: Template subdirectory (e.g., "docker", "systemd")
        extra_context: Additional Jinja2 template variables
    """
    scripts = ["start.sh", "stop.sh", "show_logs.sh", "show_status.sh"]
    context = extra_context or {}

    for script in scripts:
        template_path = deploy_instance.locate_template(f"{template_dir}/{script}.j2")
        files.template(
            name=f"Create service script {script}",
            src=str(template_path),
            dest=f"{service_dir}/{script}",
            mode="755",
            **context,
        )


class RemoteOperations:
    def __init__(self, base_deploy: "BaseDeploy") -> None:
        self.base_deploy = base_deploy

    def _create_python_env(
        self, python_path: Path, venv_path: Path, service_dir: Path | None = None
    ) -> None:
        pip.venv(
            name=f"Create Python venv: {venv_path}",
            path=str(venv_path),
            python=str(python_path),
            present=True,
        )
        if service_dir:
            files.link(
                name=f"Create symbolic link to Python venv on {service_dir}: {venv_path}",
                path=f"{service_dir}/.venv",
                target=str(venv_path),
                present=True,
                symbolic=True,
            )

    def _remove_python_env(self, venv_path: str | Path, service_dir: Path | None = None) -> None:
        pip.venv(
            name="Remove Python virtual environment",
            path=str(venv_path),
            present=False,
        )
        if service_dir:
            files.link(path=f"{service_dir}/.venv", present=False)


class BaseDeploy:
    def __init__(self) -> None:
        self._remote: RemoteOperations | None = None

    @property
    def remote(self) -> RemoteOperations:
        if getattr(self, "_remote", None) is None:
            self._remote = RemoteOperations(self)
        return self._remote

    def get_osenv_or_error(self, envname: str) -> str:
        if not envname:
            raise Exception("Environment variable name is empty")
        env_value = os.getenv(envname)
        if not env_value:
            raise Exception(f"{envname} is not configured")
        return env_value

    def _find_file_up_to_ai(self, file_path: str | Path, search_folder_name: str) -> Path | None:
        """
        Find a file by searching up the directory tree from the caller's location.

        This method automatically detects the actual deploy script location by scanning the call stack,
        making it robust against changes in wrapper method depth.

        Args:
            file_path: The file to search for
            search_folder_name: The folder name to search in (e.g., "templates")

        Returns:
            Path to the found file, or None if not found
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Find the first caller outside of runner.py (the actual deploy script)
        runner_file = Path(__file__).resolve()
        current_dir = None

        for frame_info in inspect.stack()[1:]:  # Skip this method itself
            frame_path = Path(frame_info.filename).resolve()
            # Skip frames from runner.py and find the first external caller
            if frame_path != runner_file:
                current_dir = frame_path.parent
                break

        if current_dir is None:
            # Should not happen in normal usage, but provide a safe fallback
            raise RuntimeError(
                "Could not determine caller location - all stack frames are from runner.py. "
                "This may indicate a bug in the framework."
            )

        # Search up the directory tree
        while current_dir.parent != current_dir:  # At least stop at the root
            file_checking_path = current_dir / search_folder_name / file_path
            if file_checking_path.is_file():
                return file_checking_path
            current_dir = current_dir.parent
            if (current_dir / "ai").is_dir():
                break  # Stop if we find the "ai" directory
        return None

    def locate_file(self, file_path: str | Path) -> Path:
        """
        Locate a file.

        The file can be located in any of the "files" directories in
        current and parent directories, up to (but not including) the directory
        containing the "ai" subdirectory.
        """
        result_path = self._find_file_up_to_ai(file_path, "files")
        if result_path:
            return result_path

        raise FileNotFoundError(f"The file not found: {file_path}")

    def locate_template(self, template_path: str | Path) -> Path:
        """
        Locate a template file (Jinja2 template, but not limited to).

        Templates can be located in any of the "templates" directories in
        current and parent directories, up to (but not including) the directory
        containing the "ai" subdirectory.

        The search prioritizes templates in the current directory over those in
        parent directories.

        Args:
            template_path: Path to the template file relative to templates directory
        """
        result_path = self._find_file_up_to_ai(template_path, "templates")
        if result_path:
            return result_path

        raise FileNotFoundError(f"Template file not found: {template_path}")

    def create_directories(
        self, dirs: list[Path | str] | None = None, use_sudo: bool = False
    ) -> None:
        """
        Create directories for the service.

        Args:
            dirs: List of directories to create. If None, uses [self.service_dir, self.data_dir]
            use_sudo: Whether to use sudo for directory creation. Default: False

        Examples:
            # Default: create service_dir and data_dir without sudo
            self.create_directories()

            # Custom directories with sudo
            self.create_directories(dirs=["/etc/myapp", "/var/lib/myapp"], use_sudo=True)
        """
        if dirs is None:
            dirs = []
            if hasattr(self, "service_dir") and self.service_dir:
                dirs.append(self.service_dir)
            if hasattr(self, "data_dir") and self.data_dir:
                dirs.append(self.data_dir)

        for dir_path in dirs:
            files.directory(path=str(dir_path), present=True, _sudo=use_sudo)

    def remove_directories(
        self, dirs: list[Path | str] | None = None, use_sudo: bool = True
    ) -> None:
        """
        Remove directories for the service.

        Args:
            dirs: List of directories to remove. If None, uses [self.service_dir, self.data_dir]
            use_sudo: Whether to use sudo for directory removal. Default: True

        Examples:
            # Default: remove service_dir and data_dir with sudo
            self.remove_directories()

            # Custom directories without sudo
            self.remove_directories(dirs=[self.service_dir, self.logs_dir], use_sudo=False)
        """
        if dirs is None:
            dirs = []
            if hasattr(self, "service_dir") and self.service_dir:
                dirs.append(self.service_dir)
            if hasattr(self, "data_dir") and self.data_dir:
                dirs.append(self.data_dir)

        for dir_path in dirs:
            files.directory(path=str(dir_path), present=False, _sudo=use_sudo)

    def run(self, mode: str | DeployMode) -> None:
        if isinstance(mode, str):
            mode = DeployMode(mode)
        match mode:
            case DeployMode.INSTALL:
                self.install()
            case DeployMode.REMOVE:
                self.remove()
            case DeployMode.UPDATE:
                self.update()
            case _:
                raise ConfigurationError(f"Unsupported mode: {mode}")

    def install(self) -> None:
        raise NotImplementedError

    def remove(self) -> None:
        raise NotImplementedError

    def update(self) -> None:
        logger.warning(f"{type(self).__name__} does not implement update(), skipping.")
        print(f"[BAI:UPDATE_NOT_IMPLEMENTED] {type(self).__name__}")

    def _auto_detect_template_dir(self) -> str:
        """
        Auto-detect template directory based on deployment type.

        Returns:
            "docker" for Docker Compose deployments, "systemd" for systemd deployments
        """
        # Check if this is a Docker Compose deployment
        if isinstance(self, BaseDockerComposeDeploy):
            return "docker"

        # Check if this is a Systemd deployment
        if isinstance(self, BaseSystemdDeploy):
            return "systemd"

        # Default to docker templates
        return "docker"

    def create_service_manage_scripts(
        self,
        service_dir: Path | str | None = None,
        template_dir: str | None = None,
        extra_context: dict[str, Any] | None = None,
    ) -> None:
        """
        Create standard management scripts (start/stop/logs/status) for a service.

        Args:
            service_dir: Service directory where scripts will be created (default: self.service_dir)
            template_dir: Template subdirectory (e.g., "docker", "systemd"). If None, auto-detects
            extra_context: Additional Jinja2 template variables (default: {})

        Examples:
            # Basic usage (auto-detect template_dir, no extra context)
            self.create_service_manage_scripts()

            # With extra context
            self.create_service_manage_scripts(
                extra_context={"service_name": f"backendai-{self.service_name}"}
            )

            # Custom service_dir (for coordinator/worker cases)
            self.create_service_manage_scripts(
                service_dir=self.coordinator_dir,
                template_dir="systemd",
                extra_context={"service_name": "backendai-appproxy-coordinator"}
            )
        """
        svc_dir = service_dir or getattr(self, "service_dir", None)
        if svc_dir is None:
            raise ConfigurationError(
                "service_dir must be provided or self.service_dir must be defined"
            )
        tmpl_dir = template_dir or self._auto_detect_template_dir()

        _create_management_scripts(
            deploy_instance=self,
            service_dir=svc_dir,
            template_dir=tmpl_dir,
            extra_context=extra_context or {},
        )


class BaseDockerComposeDeploy(BaseDeploy):
    """
    Base class for Docker Compose based deployments.

    Subclasses should:
    - Set self.service_dir in __init__
    - Optionally override hook methods for customization
    """

    def __init__(self) -> None:
        super().__init__()

        # Automatically set docker_compose_cmd
        self.docker_compose_cmd = get_docker_compose_cmd()

        # Subclasses must set service_dir
        self.service_dir: str | Path | None = None

        # Actual host IP for resolving host.docker.internal references
        self.host_ip: str = current_host.name
        self._host_resolve_logged = False

    def resolve_host(self, addr: str) -> str:
        """Replace host.docker.internal with actual host IP.

        Docker containers that mount /etc/hosts from the host lose the
        extra_hosts entry for host.docker.internal. Use this to substitute
        the actual host IP at deploy time.
        """
        if addr == "host.docker.internal":
            if not self._host_resolve_logged:
                self._host_resolve_logged = True
                print(f"  [INFO] Resolving 'host.docker.internal' -> '{self.host_ip}'")
            return self.host_ip
        return addr

    def create_docker_management_scripts(self, service_home: Path, user: str) -> None:
        """
        Create common Docker management scripts using shared templates.

        Args:
            service_home: The service home directory path
            user: The user to own the files
        """
        script_configs = [
            ("show_logs.sh", "docker/show_logs.sh.j2"),
            ("start.sh", "docker/start.sh.j2"),
            ("stop.sh", "docker/stop.sh.j2"),
            ("show_status.sh", "docker/show_status.sh.j2"),
        ]

        for script_name, template_name in script_configs:
            try:
                template_path = self.locate_template(template_name)
                files.template(
                    name=f"Create {script_name} script",
                    src=str(template_path),
                    dest=str(service_home / script_name),
                    mode="755",
                    user=user,
                )
            except FileNotFoundError:
                # Fallback to inline scripts if templates not found
                continue

    def load_image(
        self, container_image: str | None = None, local_archive_path: Path | str | None = None
    ) -> None:
        """
        Load Docker image from archive if available.

        Args:
            container_image: Container image name. If None, uses self.config.container_image
            local_archive_path: Archive path. If None, uses self.config.local_archive_path

        Examples:
            # Default: use config values (most common)
            self.load_image()

            # Override if needed (rare cases)
            self.load_image(container_image="custom:tag")
        """
        if not hasattr(self, "config"):
            return

        # Use provided values or fall back to config attributes
        image = (
            container_image
            if container_image is not None
            else getattr(self.config, "container_image", None)
        )
        archive = (
            local_archive_path
            if local_archive_path is not None
            else getattr(self.config, "local_archive_path", None)
        )

        if image and archive:
            load_container_image(
                container_image=image,
                local_archive_path=str(archive) if archive else None,
            )

    def start_service(self) -> None:
        server.shell(
            name="Start docker compose service",
            commands=[
                f"cd {self.service_dir}; {self.docker_compose_cmd} down",
                f"cd {self.service_dir}; {self.docker_compose_cmd} up -d",
            ],
        )

    def stop_service(self) -> None:
        server.shell(
            name="Stop docker compose service",
            commands=[f"cd {self.service_dir}; {self.docker_compose_cmd} down"],
        )

    def restart_service(self) -> None:
        self.stop_service()
        self.start_service()

    def create_env_file(self, template_name: str = "dot_env.j2", **context: Any) -> None:
        """
        Create .env file using template with custom context.

        Args:
            template_name: Template file name (default: "dot_env.j2")
            **context: Jinja2 template context variables

        Examples:
            # Basic usage with context
            self.create_env_file(
                redis_port=self.config.port,
                redis_password=self.config.password,
                container_image=self.config.container_image,
            )

            # Custom template name
            self.create_env_file(
                template_name="custom_env.j2",
                custom_var="value",
            )
        """
        # Escape '$' as '$$' for Docker Compose .env compatibility.
        # Docker Compose interprets '$' as variable substitution in .env files;
        # '$$' produces a literal '$' in the resulting environment variable.
        escaped_context: dict[str, Any] = {
            k: v.replace("$", "$$") if isinstance(v, str) else v for k, v in context.items()
        }
        files.template(
            name="Create .env file",
            src=str(self.locate_template(template_name)),
            dest=f"{self.service_dir}/.env",
            **escaped_context,
        )

    def create_docker_compose_yaml(
        self, template_name: str = "docker-compose.yml.j2", **context: Any
    ) -> None:
        """
        Create docker-compose.yml using template with custom context.

        Args:
            template_name: Template file name (default: "docker-compose.yml.j2")
            **context: Jinja2 template context variables

        Examples:
            # Basic usage with context
            self.create_docker_compose_yaml(
                data_dir=str(self.data_dir),
            )

            # Custom template name
            self.create_docker_compose_yaml(
                template_name="custom-compose.yml.j2",
                custom_var="value",
            )
        """
        files.template(
            name="Create docker-compose.yml",
            src=str(self.locate_template(template_name)),
            dest=f"{self.service_dir}/docker-compose.yml",
            **context,
        )


class BaseSystemdDeploy(BaseDeploy):
    """
    Base class for systemd based deployments.

    Subclasses should:
    - Set self.service_name in __init__
    - Optionally set self.use_sudo (default: True)
    """

    def __init__(self) -> None:
        super().__init__()

        # Subclasses must set service_name
        self.service_name: str | None = None

        # Whether to use sudo for systemd operations (default: True)
        self.use_sudo: bool = True

    def _get_full_service_name(self) -> str:
        """Get the full systemd service name."""
        if not self.service_name:
            raise MissingAttributeError("service_name", self.__class__.__name__)
        return f"backendai-{self.service_name}.service"

    def create_systemd_service(
        self,
        *,
        src: Path,
        service_name: str | None = None,
        service_dir: Path,
        exec_start: str,
        user_id: int = 0,
        group_id: int = 0,
        dest: str | None = None,
    ) -> None:
        """
        Create and enable a systemd service file.

        Args:
            src: Path to the systemd service template file
            service_name: Service name (without 'backendai-' prefix). If None, uses self.service_name
            service_dir: Working directory for the service
            exec_start: Command to execute when starting the service
            user_id: User ID to run the service as (default: 0/root)
            group_id: Group ID to run the service as (default: 0/root)
            dest: Custom destination path. If None, uses /etc/systemd/system/backendai-{service_name}.service
        """
        svc_name = service_name or self.service_name
        if not svc_name:
            raise ConfigurationError(
                "service_name must be provided or self.service_name must be set"
            )

        if dest is None:
            dest = f"/etc/systemd/system/backendai-{svc_name}.service"
            use_sudo = True
            enable_service = True
        else:
            use_sudo = False
            enable_service = False

        files.template(
            name="Create systemd service file",
            src=str(src),
            dest=dest,
            _sudo=use_sudo,
            # jinja2 context
            service_name=f"backendai-{svc_name}",
            service_dir=str(service_dir),
            description=f"Backend.AI {svc_name.title()} Service",
            exec_start=exec_start,
            user_id=user_id,
            group_id=group_id,
            working_dir=str(service_dir),
        )

        if enable_service:
            systemd.service(
                service=f"backendai-{svc_name}.service",
                enabled=True,
                daemon_reload=True,
                _sudo=True,
            )

    def remove_systemd_service(self, service_name: str | None = None) -> None:
        """
        Stop, disable, and remove a systemd service file.

        Args:
            service_name: Service name (without 'backendai-' prefix). If None, uses self.service_name
        """
        svc_name = service_name or self.service_name
        if not svc_name:
            raise ConfigurationError(
                "service_name must be provided or self.service_name must be set"
            )

        systemd.service(
            service=f"backendai-{svc_name}.service",
            running=False,
            enabled=False,
            daemon_reload=True,
            _sudo=True,
        )
        files.file(
            path=f"/etc/systemd/system/backendai-{svc_name}.service",
            present=False,
            _sudo=True,
        )

    def start_service(self) -> None:
        """Start the systemd service."""
        systemd.service(
            service=self._get_full_service_name(),
            running=True,
            _sudo=self.use_sudo,
        )

    def stop_service(self) -> None:
        """Stop the systemd service."""
        systemd.service(
            service=self._get_full_service_name(),
            running=False,
            _sudo=self.use_sudo,
        )

    def restart_service(self) -> None:
        """Restart the systemd service."""
        systemd.service(
            service=self._get_full_service_name(),
            restarted=True,
            _sudo=self.use_sudo,
        )

    def create_python_venv(
        self,
        python_path: str | Path | None = None,
        venv_path: str | Path | None = None,
        service_dir: Path | str | None = None,
    ) -> None:
        """
        Create Python virtual environment for Backend.AI services.

        Args:
            python_path: Path to Python executable. If None, uses self.python_path
            venv_path: Path for virtual environment. If None, uses self.python_venv_path
            service_dir: Service directory for symlink. If None, uses self.service_dir

        Examples:
            # Basic usage (uses self attributes)
            self.create_python_venv()

            # Custom paths
            self.create_python_venv(
                python_path="/custom/python3",
                venv_path="/custom/venv",
                service_dir="/custom/service",
            )
        """
        py_path = python_path or getattr(self, "python_path", None)
        venv = venv_path or getattr(self, "python_venv_path", None)
        svc_dir = service_dir or getattr(self, "service_dir", None)

        if not py_path or not venv:
            raise ConfigurationError(
                "python_path and venv_path must be provided or set as instance attributes"
            )

        self.remote._create_python_env(py_path, venv, svc_dir)

    def remove_python_venv(
        self,
        venv_path: str | Path | None = None,
        service_dir: Path | str | None = None,
    ) -> None:
        """
        Remove Python virtual environment.

        Args:
            venv_path: Path to virtual environment. If None, uses self.python_venv_path
            service_dir: Service directory. If None, uses self.service_dir
        """
        venv = venv_path or getattr(self, "python_venv_path", None)
        svc_dir = service_dir or getattr(self, "service_dir", None)

        if not venv:
            raise ConfigurationError("venv_path must be provided or set as instance attribute")

        self.remote._remove_python_env(venv, svc_dir)

    def install_python_packages(
        self,
        main_package: str | None = None,
        version: str | None = None,
        extra_packages: list[str] | None = None,
        pip_path: str | Path | None = None,
        pip_install_options: str | None = None,
    ) -> None:
        """
        Install Python packages for Backend.AI services.

        Args:
            main_package: Main package name (e.g., "backend.ai-manager"). If None, uses "backend.ai-{self.service_name}"
            version: Package version. If None, uses self.config_bai_core.version
            extra_packages: List of additional packages to install
            pip_path: Path to pip executable. If None, uses "{self.python_venv_path}/bin/pip"
            pip_install_options: Pip install options. If None, uses self.pip_install_options

        Examples:
            # Basic usage (installs backend.ai-{service_name})
            self.install_python_packages()

            # With extra packages
            self.install_python_packages(
                extra_packages=["backend.ai-activator", "backend.ai-accelerator-cuda"]
            )

            # Custom package and version
            self.install_python_packages(
                main_package="custom-package",
                version="1.2.3",
            )
        """
        # Determine main package name
        if main_package is None:
            if not hasattr(self, "service_name") or not self.service_name:
                raise MissingAttributeError("service_name", self.__class__.__name__)
            main_package = f"backend.ai-{self.service_name}"

        # Get version
        pkg_version = version or getattr(getattr(self, "config_bai_core", None), "version", None)
        if not pkg_version:
            raise ConfigurationError(
                "version must be provided or self.config_bai_core.version must be set"
            )

        # Get pip path
        pip_exec = pip_path or f"{getattr(self, 'python_venv_path', None)}/bin/pip"
        if not getattr(self, "python_venv_path", None) and not pip_path:
            raise ConfigurationError(
                "pip_path must be provided or self.python_venv_path must be set"
            )

        # Get pip install options
        install_opts = pip_install_options or getattr(self, "pip_install_options", "")

        # Install main package
        pip.packages(
            name=f"Install {main_package} version {pkg_version}",
            packages=[f"{main_package}=={pkg_version}"],
            extra_install_args=install_opts,
            pip=pip_exec,
            present=True,
        )

        # Install extra packages
        if extra_packages:
            for package in extra_packages:
                pip.packages(
                    name=f"Install {package}",
                    packages=[package],
                    extra_install_args=install_opts,
                    pip=pip_exec,
                    present=True,
                )

    def create_toml_config(
        self,
        template_name: str | None = None,
        dest_path: str | Path | None = None,
        create_symlink: bool = True,
        **context: Any,
    ) -> None:
        """
        Create TOML configuration file from template.

        Args:
            template_name: Template file name. If None, uses "{self.service_name}.toml.j2"
            dest_path: Destination path. If None, uses "~/.config/backend.ai/{self.service_name}.toml"
            create_symlink: Whether to create symlink in service_dir (default: True)
            **context: Jinja2 template context variables

        Examples:
            # Basic usage (auto-detect template and destination)
            self.create_toml_config(
                home_dir=self.home_dir,
                service_name=self.service_name,
                etcd_ip=self.config_etcd.hostname,
            )

            # Custom template and destination
            self.create_toml_config(
                template_name="custom.toml.j2",
                dest_path="/etc/myapp/config.toml",
                create_symlink=False,
                custom_var="value",
            )
        """
        # Determine template name
        if template_name is None:
            if not hasattr(self, "service_name") or not self.service_name:
                raise MissingAttributeError("service_name", self.__class__.__name__)
            template_name = f"{self.service_name}.toml.j2"

        # Determine destination path
        if dest_path is None:
            if not hasattr(self, "home_dir") or not self.home_dir:
                raise MissingAttributeError("home_dir", self.__class__.__name__)
            if not hasattr(self, "service_name") or not self.service_name:
                raise MissingAttributeError("service_name", self.__class__.__name__)
            dest_path = f"{self.home_dir}/.config/backend.ai/{self.service_name}.toml"

        # Create configuration file
        files.template(
            name="Create TOML configuration file",
            src=str(self.locate_template(template_name)),
            dest=str(dest_path),
            **context,
        )

        # Create symlink if requested
        if create_symlink:
            if not hasattr(self, "service_dir") or not self.service_dir:
                raise MissingAttributeError("service_dir", self.__class__.__name__)

            symlink_name = f"{getattr(self, 'service_name', 'config')}.toml"
            files.link(
                path=f"{self.service_dir}/{symlink_name}",
                target=str(dest_path),
                present=True,
                symbolic=True,
            )

    def remove_toml_config(self, config_path: str | Path | None = None) -> None:
        """
        Remove TOML configuration file.

        Args:
            config_path: Path to configuration file. If None, uses "~/.config/backend.ai/{self.service_name}.toml"
        """
        if config_path is None:
            if not hasattr(self, "home_dir") or not hasattr(self, "service_name"):
                raise ConfigurationError(
                    "home_dir and service_name must be set to use default config_path"
                )
            config_path = f"{self.home_dir}/.config/backend.ai/{self.service_name}.toml"

        files.file(path=str(config_path), present=False)

    def create_run_script(
        self,
        template_name: str | None = None,
        script_name: str | None = None,
        dest_dir: str | Path | None = None,
        **context: Any,
    ) -> None:
        """
        Create service run script from template.

        Args:
            template_name: Template file name. If None, uses "run-{self.service_name}.sh.j2"
            script_name: Script file name. If None, uses "run-{self.service_name}.sh"
            dest_dir: Destination directory. If None, uses "{self.home_dir}/bin"
            **context: Jinja2 template context variables

        Examples:
            # Basic usage (auto-detect paths)
            self.create_run_script(
                home_dir=self.home_dir,
                service_name=self.service_name,
                redis_ip=self.config_redis.hostname,
            )

            # Custom template and script name
            self.create_run_script(
                template_name="custom-runner.sh.j2",
                script_name="start-service.sh",
                dest_dir="/usr/local/bin",
                custom_var="value",
            )
        """
        # Determine template name
        if template_name is None:
            if not hasattr(self, "service_name") or not self.service_name:
                raise MissingAttributeError("service_name", self.__class__.__name__)
            template_name = f"run-{self.service_name}.sh.j2"

        # Determine script name
        if script_name is None:
            if not hasattr(self, "service_name") or not self.service_name:
                raise MissingAttributeError("service_name", self.__class__.__name__)
            script_name = f"run-{self.service_name}.sh"

        # Determine destination directory
        if dest_dir is None:
            if not hasattr(self, "home_dir") or not self.home_dir:
                raise MissingAttributeError("home_dir", self.__class__.__name__)
            dest_dir = f"{self.home_dir}/bin"

        # Create run script
        files.template(
            name=f"Create run script: {script_name}",
            src=str(self.locate_template(template_name)),
            dest=f"{dest_dir}/{script_name}",
            mode="755",
            **context,
        )

    def remove_run_script(
        self,
        script_name: str | None = None,
        script_dir: str | Path | None = None,
    ) -> None:
        """
        Remove service run script.

        Args:
            script_name: Script file name. If None, uses "run-{self.service_name}.sh"
            script_dir: Script directory. If None, uses "{self.home_dir}/bin"
        """
        if script_name is None:
            if not hasattr(self, "service_name") or not self.service_name:
                raise MissingAttributeError("service_name", self.__class__.__name__)
            script_name = f"run-{self.service_name}.sh"

        if script_dir is None:
            if not hasattr(self, "home_dir") or not self.home_dir:
                raise MissingAttributeError("home_dir", self.__class__.__name__)
            script_dir = f"{self.home_dir}/bin"

        files.file(path=f"{script_dir}/{script_name}", present=False)

    def get_otel_collector_config(self, host_data: Any) -> Any:
        """Get OTEL config, checking 'otel_collector' then 'otel_collector_config'."""
        return host_data.services.get("otel_collector") or host_data.services.get(
            "otel_collector_config"
        )

    def get_otel_collector_endpoint(self, otel_config: Any = None) -> str | None:
        """Generate OTEL Collector gRPC endpoint URL (e.g., 'http://collector:4317')."""
        config = otel_config or getattr(self, "config_otel_collector", None)
        if not config:
            return None
        return f"http://{config.hostname}:{config.grpc_port}"
