from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId


class IPUDevice(AbstractComputeDevice):
    model_name: str
    serial: DeviceId
    ip: str

    def __init__(self, model_name: str, serial: DeviceId, ip: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.serial = serial
        self.ip = ip

    def __str__(self) -> str:
        return f"IPUDevice <{self.hw_location}>"

    def __repr__(self) -> str:
        return self.__str__()
