from pathlib import Path

from ai.backend.agent.resources import AbstractComputeDevice

__all__ = ("LPUDevice",)


class LPUDevice(AbstractComputeDevice):
    model_name: str
    device_number: int

    xvc_pri_path: Path
    renderD_path: Path

    def __init__(
        self,
        model_name: str,
        device_number: int,
        xvc_pri_path: Path,
        renderD_path: Path,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.device_number = device_number
        self.xvc_pri_path = xvc_pri_path
        self.renderD_path = renderD_path

    def __str__(self) -> str:
        return f"LPUDevice <{self.hw_location}>"

    def __repr__(self) -> str:
        return self.__str__()
