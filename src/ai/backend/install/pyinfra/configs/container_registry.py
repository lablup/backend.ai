from pydantic import BaseModel


class HarborRegistryConfig(BaseModel):
    admin_password: str

    # Harbor download URL or path to the offline installer
    download_uri: str = "https://github.com/goharbor/harbor/releases/download/v2.10.3/harbor-offline-installer-v2.10.3.tgz"

    # Path to kernel images directory for loading into Harbor
    # Can be a local path or HTTP URL (e.g., "http://bai-repo:9200/kernel/")
    kernel_images_path: str = ""

    # Custom data directory for Harbor storage
    # If empty, defaults to {bai_home_dir}/.data/harbor
    data_dir: str = ""

    # Enable Trivy vulnerability scanner in Harbor
    enable_trivy: bool = False
