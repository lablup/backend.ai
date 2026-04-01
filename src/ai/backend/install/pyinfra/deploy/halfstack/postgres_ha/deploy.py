import importlib.util
from pathlib import Path

from pyinfra import host

from ai.backend.install.pyinfra.runner import BaseDeploy


class PostgresHADeploy(BaseDeploy):
    def __init__(self, host_data: object, service_key: str = "postgres_ha") -> None:
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_key = service_key
        self.config = host_data.services[service_key]
        # Use appropriate cluster_info based on service_key
        if service_key == "controlpanel":
            self.pg_cluster_info = getattr(host_data, "cp_pg_cluster_info", {})
        else:
            self.pg_cluster_info = getattr(host_data, "pg_cluster_info", {})

    def deploy_postgres_cluster(self) -> None:
        module_path = Path(__file__).parent / "postgres_cluster" / "deploy.py"
        spec = importlib.util.spec_from_file_location("postgres_cluster.deploy", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PostgresClusterDeploy(host.data, service_key=self.service_key).install()

    def deploy_postgres_etcd(self) -> None:
        module_path = Path(__file__).parent / "postgres_etcd" / "deploy.py"
        spec = importlib.util.spec_from_file_location("postgres_etcd.deploy", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PostgresEtcdDeploy(host.data, service_key=self.service_key).install()

    def deploy_postgres_haproxy(self) -> None:
        module_path = Path(__file__).parent / "postgres_haproxy" / "deploy.py"
        spec = importlib.util.spec_from_file_location("postgres_haproxy.deploy", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PostgresHaproxyDeploy(host.data, service_key=self.service_key).install()

    def remove_postgres_cluster(self) -> None:
        module_path = Path(__file__).parent / "postgres_cluster" / "deploy.py"
        spec = importlib.util.spec_from_file_location("postgres_cluster.deploy", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PostgresClusterDeploy(host.data, service_key=self.service_key).remove()

    def remove_postgres_etcd(self) -> None:
        module_path = Path(__file__).parent / "postgres_etcd" / "deploy.py"
        spec = importlib.util.spec_from_file_location("postgres_etcd.deploy", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PostgresEtcdDeploy(host.data, service_key=self.service_key).remove()

    def remove_postgres_haproxy(self) -> None:
        module_path = Path(__file__).parent / "postgres_haproxy" / "deploy.py"
        spec = importlib.util.spec_from_file_location("postgres_haproxy.deploy", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.PostgresHaproxyDeploy(host.data, service_key=self.service_key).remove()

    def install(self) -> None:
        print(
            f"Deploying PostgreSQL HA ({self.config.name}) on node: {self.pg_cluster_info.get('node_name', 'unknown')}"
        )

        # Deploy all three components
        self.deploy_postgres_etcd()
        self.deploy_postgres_cluster()
        self.deploy_postgres_haproxy()

    def remove(self) -> None:
        print(
            f"Removing PostgreSQL HA ({self.config.name}) from node: {self.pg_cluster_info.get('node_name', 'unknown')}"
        )

        # Remove all three components
        self.remove_postgres_haproxy()
        self.remove_postgres_etcd()
        self.remove_postgres_cluster()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    service_key = host.data.get("service_key", "postgres_ha")
    PostgresHADeploy(host.data, service_key=service_key).run(deploy_mode)


main()
