from pyinfra import host

from ai.backend.install.pyinfra.deploy.cores.appproxy.worker_base import AppProxyWorkerBaseDeploy


class AppProxyWorkerInteractiveDeploy(AppProxyWorkerBaseDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__(host_data, "interactive")


# Execute deployment when script is loaded
def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    AppProxyWorkerInteractiveDeploy(host.data).run(deploy_mode)


main()
