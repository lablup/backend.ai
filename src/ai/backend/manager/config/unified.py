from typing import Awaitable, Callable

from ai.backend.manager.config.watchers.types import AbstractConfigController

from .loader.etcd_loader import LegacyEtcdLoader
from .loader.types import AbstractConfigLoader
from .local import ManagerLocalConfig
from .shared import ManagerSharedConfig

SharedConfigChangeCallback = Callable[[ManagerSharedConfig], Awaitable[None]]


class ManagerUnifiedConfig:
    local: ManagerLocalConfig
    shared: ManagerSharedConfig
    local_config_loader: AbstractConfigLoader
    etcd_config_loader: LegacyEtcdLoader

    config_controllers: list[AbstractConfigController]

    def __init__(
        self,
        local: ManagerLocalConfig,
        shared: ManagerSharedConfig,
        local_config_loader: AbstractConfigLoader,
        shared_config_loader: LegacyEtcdLoader,
        config_controllers: list[AbstractConfigController] = [],
    ) -> None:
        self.local = local
        self.shared = shared
        self.local_config_loader = local_config_loader
        self.etcd_config_loader = shared_config_loader
        self.config_controllers = config_controllers
