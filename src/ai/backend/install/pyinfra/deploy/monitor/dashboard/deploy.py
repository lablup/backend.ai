import importlib.util
from pathlib import Path

from pyinfra import host
from pyinfra.operations import files

from ai.backend.install.pyinfra.runner import BaseDeploy


class DashboardDeploy(BaseDeploy):
    def __init__(self, host_data: object) -> None:
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "dashboard"
        self.service_home = Path(f"{self.home_dir}/dashboard")

        # Service deployment order (by directory name)
        # NOTE: dcgm_exporter is NOT included here — it deploys to agent/compute
        # nodes (not the dashboard node) via its own registry.py entry.
        self.exporter_services = ["postgres_exporter", "redis_exporter", "blackbox_exporter"]
        self.core_services = ["prometheus", "loki", "otel_collector", "pyroscope"]
        self.grafana_service = "grafana"

    def _load_and_execute_deploy(self, service_dir: str, method_name: str) -> None:
        """
        Dynamically load a service deployment module and execute specified method.

        Args:
            service_dir: Service directory name (e.g., "prometheus", "grafana")
            method_name: Method name to execute (e.g., "install", "remove")
        """
        module_path = Path(__file__).parent / service_dir / "deploy.py"
        spec = importlib.util.spec_from_file_location(f"{service_dir}.deploy", module_path)

        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the deploy class (assumes pattern: *Deploy)
        # Only consider classes defined in this module, not imported base classes
        deploy_class = None
        for name in dir(module):
            if name.endswith("Deploy") and name not in ("BaseDeploy", "BaseDockerComposeDeploy"):
                obj = getattr(module, name)
                # Check if this class is defined in the current module
                if hasattr(obj, "__module__") and obj.__module__ == module.__name__:
                    deploy_class = obj
                    break

        if deploy_class is None:
            raise ImportError(f"No Deploy class found in {module_path}")

        # Execute method
        deploy_instance = deploy_class(host.data)
        getattr(deploy_instance, method_name)()

    def deploy_service(self, service_dir: str) -> None:
        """Deploy a single service"""
        print(f"  - Deploying {service_dir}...")
        self._load_and_execute_deploy(service_dir, "install")

    def remove_service(self, service_dir: str) -> None:
        """Remove a single service"""
        print(f"  - Removing {service_dir}...")
        self._load_and_execute_deploy(service_dir, "remove")

    def create_service_home_directory(self) -> None:
        """Create the dashboard base directory"""
        files.directory(path=str(self.service_home), present=True, user=self.user)

    def remove_service_home_directory(self) -> None:
        """Remove the dashboard base directory"""
        files.directory(path=str(self.service_home), present=False, user=self.user)

    def install(self) -> None:
        print("Deploying all dashboard components...")

        self.create_service_home_directory()

        for service in self.exporter_services:
            self.deploy_service(service)
        for service in self.core_services:
            self.deploy_service(service)
        self.deploy_service(self.grafana_service)

    def remove(self) -> None:
        print("Removing all dashboard components...")

        self.remove_service(self.grafana_service)
        for service in reversed(self.core_services):
            self.remove_service(service)
        for service in reversed(self.exporter_services):
            self.remove_service(service)

        self.remove_service_home_directory()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = DashboardDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
