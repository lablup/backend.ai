import importlib.util
from pathlib import Path
from typing import Any

from pyinfra import host

from ai.backend.install.pyinfra.runner import BaseDeploy
from ai.backend.install.pyinfra.utils import get_major_version

SERVICE_DIR = "{home_dir}/appproxy"
COORDINATOR_DIR = "{service_dir}/coordinator"
WORKER_DIR_TEMPLATE = "{service_dir}/worker-{worker_type}"
TRAEFIK_DIR = "{service_dir}/traefik"
WORKER_TYPES = ["interactive", "inference", "tcp"]


def create_worker_configs(service_dir: Path, config: object) -> dict[str, dict[str, Any]]:
    worker_configs = {}
    for worker_type in WORKER_TYPES:
        worker_dir = Path(
            WORKER_DIR_TEMPLATE.format(service_dir=service_dir, worker_type=worker_type)
        )
        worker_configs[worker_type] = {
            "dir": worker_dir,
            "advertised_hostname": getattr(config, f"worker_{worker_type}_advertised_hostname"),
            "port": getattr(config, f"worker_{worker_type}_port"),
            "authority": f"worker-{config.worker_node_number}-{worker_type}",
            "aiomonitor_termui_port": getattr(
                config, f"worker_{worker_type}_aiomonitor_termui_port"
            ),
            "aiomonitor_webui_port": getattr(config, f"worker_{worker_type}_aiomonitor_webui_port"),
            "protocol": "tcp" if worker_type == "tcp" else "http",
            "accepted_traffic": "inference" if worker_type == "inference" else "interactive",
            "app_port_start": getattr(config, f"worker_{worker_type}_app_port_start"),
            "app_port_end": getattr(config, f"worker_{worker_type}_app_port_end"),
            "traefik_api_port": getattr(
                config,
                f"worker_{worker_type}_traefik_api_port",
                9090 + WORKER_TYPES.index(worker_type),
            ),
            "service_name": f"appproxy-worker-{worker_type}",
            "run_script_name": f"run-appproxy-worker-{worker_type}.sh",
        }
    return worker_configs


class AppProxyDeploy(BaseDeploy):
    def __init__(self, host_data: object) -> None:
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.user_id = host_data.bai_user_id
        self.group_id = host_data.bai_user_group_id

        self.config = host_data.services["appproxy"]
        self.config_db = host_data.services["postgres"]
        self.config_redis = host_data.services["redis"]
        self.config_bai_core = host_data.services["bai_core"]
        self.config_etcd = host_data.services.get("etcd", None)

        self.appproxy_major_version = get_major_version(self.config_bai_core.version)
        self.pip_install_options = host_data.bai_pip_install_options
        self.python_version = host_data.python_version
        self.python_path = (
            f"{self.home_dir}/.static-python/versions/{self.python_version}/bin/python3"
        )

        self.python_coordinator_venv_path = f"{self.home_dir}/.static-python/venvs/bai-{self.appproxy_major_version}-appproxy-coordinator"
        self.python_worker_venv_path = f"{self.home_dir}/.static-python/venvs/bai-{self.appproxy_major_version}-appproxy-worker"

        self.service_dir = Path(SERVICE_DIR.format(home_dir=self.home_dir))
        self.coordinator_dir = Path(COORDINATOR_DIR.format(service_dir=self.service_dir))
        self.traefik_dir = Path(TRAEFIK_DIR.format(service_dir=self.service_dir))
        self.worker_types = WORKER_TYPES
        self.worker_configs = create_worker_configs(self.service_dir, self.config)

    def deploy_coordinator(self) -> None:
        """Deploy AppProxy coordinator component"""
        module_path = Path(__file__).parent / "coordinator" / "deploy.py"
        spec = importlib.util.spec_from_file_location("coordinator.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyCoordinatorDeploy(host.data).install()

    def deploy_worker_interactive(self) -> None:
        """Deploy AppProxy interactive worker component"""
        module_path = Path(__file__).parent / "worker_interactive" / "deploy.py"
        spec = importlib.util.spec_from_file_location("worker_interactive.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyWorkerInteractiveDeploy(host.data).install()

    def deploy_worker_inference(self) -> None:
        """Deploy AppProxy inference worker component"""
        module_path = Path(__file__).parent / "worker_inference" / "deploy.py"
        spec = importlib.util.spec_from_file_location("worker_inference.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyWorkerInferenceDeploy(host.data).install()

    def deploy_worker_tcp(self) -> None:
        """Deploy AppProxy TCP worker component"""
        module_path = Path(__file__).parent / "worker_tcp" / "deploy.py"
        spec = importlib.util.spec_from_file_location("worker_tcp.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyWorkerTcpDeploy(host.data).install()

    def deploy_traefik(self) -> None:
        """Deploy AppProxy Traefik component for all worker types"""
        module_path = Path(__file__).parent / "traefik" / "deploy.py"
        spec = importlib.util.spec_from_file_location("traefik.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyTraefikDeploy(host.data).install()

    def deploy_traefik_for_worker(self, worker_type: str) -> None:
        """Deploy AppProxy Traefik component for a specific worker type"""
        module_path = Path(__file__).parent / "traefik" / "deploy.py"
        spec = importlib.util.spec_from_file_location("traefik.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyTraefikDeploy(host.data).install_for_worker(worker_type)

    def remove_coordinator(self) -> None:
        """Remove AppProxy coordinator component"""
        module_path = Path(__file__).parent / "coordinator" / "deploy.py"
        spec = importlib.util.spec_from_file_location("coordinator.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyCoordinatorDeploy(host.data).remove()

    def remove_worker_interactive(self) -> None:
        """Remove AppProxy interactive worker component"""
        module_path = Path(__file__).parent / "worker_interactive" / "deploy.py"
        spec = importlib.util.spec_from_file_location("worker_interactive.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyWorkerInteractiveDeploy(host.data).remove()

    def remove_worker_inference(self) -> None:
        """Remove AppProxy inference worker component"""
        module_path = Path(__file__).parent / "worker_inference" / "deploy.py"
        spec = importlib.util.spec_from_file_location("worker_inference.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyWorkerInferenceDeploy(host.data).remove()

    def remove_worker_tcp(self) -> None:
        """Remove AppProxy TCP worker component"""
        module_path = Path(__file__).parent / "worker_tcp" / "deploy.py"
        spec = importlib.util.spec_from_file_location("worker_tcp.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyWorkerTcpDeploy(host.data).remove()

    def remove_traefik(self) -> None:
        """Remove AppProxy Traefik component for all worker types"""
        module_path = Path(__file__).parent / "traefik" / "deploy.py"
        spec = importlib.util.spec_from_file_location("traefik.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyTraefikDeploy(host.data).remove()

    def remove_traefik_for_worker(self, worker_type: str) -> None:
        """Remove AppProxy Traefik component for a specific worker type"""
        module_path = Path(__file__).parent / "traefik" / "deploy.py"
        spec = importlib.util.spec_from_file_location("traefik.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyTraefikDeploy(host.data).remove_for_worker(worker_type)

    def install(self) -> None:
        """Install all AppProxy components"""
        print("Deploying all AppProxy components...")

        # Deploy coordinator
        self.deploy_coordinator()

        # Deploy all worker types
        self.deploy_worker_interactive()
        self.deploy_worker_inference()
        self.deploy_worker_tcp()

        # Deploy Traefik for all workers
        self.deploy_traefik()

    def remove(self) -> None:
        """Remove all AppProxy components"""
        print("Removing all AppProxy components...")

        # Remove Traefik for all workers
        self.remove_traefik()

        # Remove all worker types
        self.remove_worker_interactive()
        self.remove_worker_inference()
        self.remove_worker_tcp()

        # Remove coordinator
        self.remove_coordinator()

        # Clean up shared worker venv
        self.remote._remove_python_env(self.python_worker_venv_path, self.service_dir)

    def update_coordinator(self) -> None:
        """Update AppProxy coordinator component"""
        module_path = Path(__file__).parent / "coordinator" / "deploy.py"
        spec = importlib.util.spec_from_file_location("coordinator.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyCoordinatorDeploy(host.data).update()

    def update_worker_interactive(self) -> None:
        """Update AppProxy interactive worker component"""
        module_path = Path(__file__).parent / "worker_interactive" / "deploy.py"
        spec = importlib.util.spec_from_file_location("worker_interactive.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyWorkerInteractiveDeploy(host.data).update()

    def update_worker_inference(self) -> None:
        """Update AppProxy inference worker component"""
        module_path = Path(__file__).parent / "worker_inference" / "deploy.py"
        spec = importlib.util.spec_from_file_location("worker_inference.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyWorkerInferenceDeploy(host.data).update()

    def update_worker_tcp(self) -> None:
        """Update AppProxy TCP worker component"""
        module_path = Path(__file__).parent / "worker_tcp" / "deploy.py"
        spec = importlib.util.spec_from_file_location("worker_tcp.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.AppProxyWorkerTcpDeploy(host.data).update()

    def update(self) -> None:
        """Update all AppProxy components"""
        print("Updating all AppProxy components...")

        # Update coordinator
        self.update_coordinator()

        # Update all worker types
        self.update_worker_interactive()
        self.update_worker_inference()
        self.update_worker_tcp()

        print("\n=== AppProxy Update Complete ===")
        print("Review changes for each component:")
        print(f"  - Coordinator: {self.coordinator_dir}/upgrades/show_diffs.sh")
        for worker_type in self.worker_types:
            worker_dir = self.worker_configs[worker_type]["dir"]
            print(f"  - Worker ({worker_type}): {worker_dir}/upgrades/show_diffs.sh")


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    AppProxyDeploy(host.data).run(deploy_mode)


main()
