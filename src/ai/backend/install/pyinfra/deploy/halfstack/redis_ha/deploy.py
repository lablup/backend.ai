import importlib.util
from pathlib import Path

from pyinfra import host

from ai.backend.install.pyinfra.runner import BaseDeploy


class RedisHADeploy(BaseDeploy):
    def __init__(self, host_data: object) -> None:
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.config = host_data.services["redis_ha"]
        self.redis_cluster_info = getattr(host_data, "redis_cluster_info", {})

    def _load_submodule_class(self, submodule_name: str, class_name: str) -> type:
        """
        Load and return a deploy class from a submodule.

        Args:
            submodule_name: Name of the submodule directory (e.g., "redis_cluster")
            class_name: Name of the class to load (e.g., "RedisClusterDeploy")

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

    def deploy_redis_cluster(self) -> None:
        deploy_class = self._load_submodule_class("redis_cluster", "RedisClusterDeploy")
        deploy_class(host.data).install()

    def deploy_redis_sentinel(self) -> None:
        deploy_class = self._load_submodule_class("redis_sentinel", "RedisSentinelDeploy")
        deploy_class(host.data).install()

    def deploy_redis_haproxy(self) -> None:
        deploy_class = self._load_submodule_class("redis_haproxy", "RedisHaproxyDeploy")
        deploy_class(host.data).install()

    def remove_redis_cluster(self) -> None:
        deploy_class = self._load_submodule_class("redis_cluster", "RedisClusterDeploy")
        deploy_class(host.data).remove()

    def remove_redis_sentinel(self) -> None:
        deploy_class = self._load_submodule_class("redis_sentinel", "RedisSentinelDeploy")
        deploy_class(host.data).remove()

    def remove_redis_haproxy(self) -> None:
        deploy_class = self._load_submodule_class("redis_haproxy", "RedisHaproxyDeploy")
        deploy_class(host.data).remove()

    def install(self) -> None:
        print(
            f"Deploying Redis HA components on node: {self.redis_cluster_info.get('node_name', 'unknown')}"
        )

        # Deploy all three components in dependency order
        self.deploy_redis_cluster()
        self.deploy_redis_sentinel()
        self.deploy_redis_haproxy()

    def remove(self) -> None:
        print(
            f"Removing Redis HA components from node: {self.redis_cluster_info.get('node_name', 'unknown')}"
        )

        # Remove all three components in reverse order
        self.remove_redis_haproxy()
        self.remove_redis_sentinel()
        self.remove_redis_cluster()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    RedisHADeploy(host.data).run(deploy_mode)


main()
