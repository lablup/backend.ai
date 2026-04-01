from pyinfra import host

from ai.backend.install.pyinfra.deploy.cores.appproxy.worker_base import AppProxyWorkerBaseDeploy


class AppProxyWorkerInferenceDeploy(AppProxyWorkerBaseDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__(host_data, "inference")


# Execute deployment when script is loaded
def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = AppProxyWorkerInferenceDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    elif deploy_mode == "update":
        deploy.update()
    else:
        deploy.install()


main()
