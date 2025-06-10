from dataclasses import dataclass


@dataclass
class KernelCreationArgs:
    kernel_id: str
    session_id: str
    image_ref: str
    environ: dict[str, str]

    is_debug: bool  # resource_spec: dict[str, str]
