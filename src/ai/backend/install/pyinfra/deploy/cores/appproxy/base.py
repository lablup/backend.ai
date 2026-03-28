from pyinfra.operations import pip

from ai.backend.install.pyinfra.runner import BaseSystemdDeploy
from ai.backend.install.pyinfra.utils import ensure_file_exists, get_major_version


class AppProxyBaseDeploy(BaseSystemdDeploy):
    """Base class for AppProxy component deployments with common functionality."""

    def _init_common_properties(self, host_data: object) -> None:
        """Initialize common properties shared across all AppProxy components."""
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.user_id = host_data.bai_user_id
        self.group_id = host_data.bai_user_group_id

        self.config = host_data.services["appproxy"]
        self.config_redis = host_data.services["redis"]
        self.config_bai_core = host_data.services["bai_core"]
        self.config_etcd = host_data.services.get("etcd", None)
        self.config_otel_collector = self.get_otel_collector_config(host_data)

        self.appproxy_major_version = get_major_version(self.config_bai_core.version)
        self.pip_install_options = host_data.bai_pip_install_options

    def _init_python_env(self, host_data: object) -> None:
        """Initialize Python environment paths."""
        self.python_version = host_data.python_version
        self.python_path = (
            f"{self.home_dir}/.static-python/versions/{self.python_version}/bin/python3"
        )

    def _install_package(self, name: str, venv_path: str, package_uris: list[str]) -> None:
        """Install packages from URI sources."""
        valid_uris = [uri for uri in package_uris if uri is not None]
        if valid_uris:
            for uri in valid_uris:
                ensure_file_exists(uri)
            pip.packages(
                name=f"Install {name}",
                packages=valid_uris,
                extra_install_args=self.pip_install_options,
                pip=f"{venv_path}/bin/pip",
                present=True,
            )

    def _install_package_by_name(self, name: str, venv_path: str, package_names: list[str]) -> None:
        """Install packages by name from PyPI."""
        pip.packages(
            name=f"Install {name} from PyPI",
            packages=package_names,
            extra_install_args=self.pip_install_options,
            pip=f"{venv_path}/bin/pip",
            present=True,
        )
