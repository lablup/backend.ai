import importlib.util
from pathlib import Path

from pyinfra import host

from ai.backend.install.pyinfra.runner import BaseDeploy


class EtcdHADeploy(BaseDeploy):
    def __init__(self, host_data: object) -> None:
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.config = host_data.services["etcd_ha"]
        self.etcd_cluster_info = getattr(host_data, "etcd_cluster_info", {})

    def _load_submodule_class(self, submodule_name: str, class_name: str) -> type:
        """
        Load and return a deploy class from a submodule.

        Args:
            submodule_name: Name of the submodule directory (e.g., "etcd_cluster")
            class_name: Name of the class to load (e.g., "EtcdClusterDeploy")

        Returns:
            The deploy class from the submodule
        """
        module_path = Path(__file__).parent / submodule_name / "deploy.py"
        spec = importlib.util.spec_from_file_location(f"{submodule_name}.deploy", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name)

    def deploy_etcd_cluster(self) -> None:
        deploy_class = self._load_submodule_class("etcd_cluster", "EtcdClusterDeploy")
        deploy_class(host.data).install()

    def deploy_etcd_grpc(self) -> None:
        deploy_class = self._load_submodule_class("etcd_grpc", "EtcdGrpcDeploy")
        deploy_class(host.data).install()

    def remove_etcd_cluster(self) -> None:
        deploy_class = self._load_submodule_class("etcd_cluster", "EtcdClusterDeploy")
        deploy_class(host.data).remove()

    def remove_etcd_grpc(self) -> None:
        deploy_class = self._load_submodule_class("etcd_grpc", "EtcdGrpcDeploy")
        deploy_class(host.data).remove()

    def install(self) -> None:
        print(
            f"Deploying ETCD HA components on node: {self.etcd_cluster_info.get('node_name', 'unknown')}"
        )

        # Deploy ETCD cluster first, then gRPC proxy
        self.deploy_etcd_cluster()
        self.deploy_etcd_grpc()

    def remove(self) -> None:
        print(
            f"Removing ETCD HA components from node: {self.etcd_cluster_info.get('node_name', 'unknown')}"
        )

        # Remove in reverse order
        self.remove_etcd_grpc()
        self.remove_etcd_cluster()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    EtcdHADeploy(host.data).run(deploy_mode)


main()
