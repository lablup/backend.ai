"""
Global host.data defaults for all pyinfra hosts.

These module-level variables are loaded by pyinfra's group_data mechanism
and become accessible as `host.data.<variable_name>` in deploy scripts.

All values can be overridden via environment variables (PYINFRA_* prefix)
or per-host in the inventory file.
"""

import json
import os

from dotenv import load_dotenv
from pyinfra import logger

load_dotenv()


# -- SSH configuration
ssh_user = os.getenv("PYINFRA_SSH_USER", "bai")
ssh_key = os.getenv("PYINFRA_SSH_KEY", "~/.ssh/id_rsa")
ssh_pubkey = os.getenv("PYINFRA_SSH_PUBKEY", "~/.ssh/id_rsa.pub")
ssh_port = int(os.getenv("PYINFRA_SSH_PORT", "22"))
ssh_password = os.getenv("PYINFRA_SSH_PASSWORD", "")
ssh_strict_host_key_checking = "no"

if not os.getenv("PYINFRA_SUDO_PASSWORD"):
    logger.warning("Set PYINFRA_SUDO_PASSWORD to run sudo without password input")


# -- Offline repositories
bai_offline_repo_url = os.getenv("PYINFRA_BAI_OFFLINE_REPO_URL", "http://bai-repo:9200")
bai_offline_apt_url = os.getenv(
    "PYINFRA_BAI_OFFLINE_APT_URL", "http://bai-repo:9200/apt/22.04/x86_64"
)
bai_pip_install_options = os.getenv("PYINFRA_BAI_PIP_INSTALL_OPTIONS")


# -- OS configuration
bai_home_dir = os.getenv("PYINFRA_BAI_HOME_DIR", "/home/bai")
bai_user = os.getenv("PYINFRA_BAI_USER", "bai")
bai_user_id = int(os.getenv("PYINFRA_BAI_USER_ID", "1100"))
bai_user_group_id = int(os.getenv("PYINFRA_BAI_USER_GROUP_ID", "1100"))
bai_user_password = os.getenv("PYINFRA_BAI_USER_PASSWORD")

enable_passwordless_sudo = os.getenv("PYINFRA_ENABLE_PASSWORDLESS_SUDO", "false").lower() == "true"

bai_file_block_marker = os.getenv("PYINFRA_BAI_FILE_BLOCK_MARKER", "# -- {mark} Backend.AI")
bai_fstab_contents_path = os.getenv("PYINFRA_BAI_FSTAB_CONTENTS_PATH", "./_files/etc_fstab")
bai_hosts_contents_path = os.getenv("PYINFRA_BAI_HOSTS_CONTENTS_PATH", "./_files/etc_hosts")


# -- Docker
docker_installation_uri = os.getenv(
    "PYINFRA_DOCKER_INSTALLATION_URI", "https://download.docker.com"
)
docker_installation_os = os.getenv("PYINFRA_DOCKER_OS", "linux")
docker_installation_distro = os.getenv("PYINFRA_DOCKER_DISTRO", "ubuntu")
docker_data_root = os.getenv("PYINFRA_DOCKER_DATA_ROOT")
docker_default_address_pools_str = os.getenv("PYINFRA_DOCKER_DEFAULT_ADDRESS_POOLS", "[]")
docker_compose_offline_path = os.getenv(
    "PYINFRA_DOCKER_COMPOSE_OFFLINE_PATH", "custom/docker-compose-linux-{arch}"
)
try:
    docker_default_address_pools = json.loads(docker_default_address_pools_str)
except json.JSONDecodeError:
    logger.warning("Invalid JSON format for PYINFRA_DOCKER_DEFAULT_ADDRESS_POOLS")
    docker_default_address_pools = []


# -- Python
python_version = os.getenv("PYINFRA_PYTHON_VERSION", "3.12.7")
indygreg_python_release_date = os.getenv("PYINFRA_INDYGREG_PYTHON_RELEASE_DATE", "20241008")
indygreg_python_archive = os.getenv(
    "PYINFRA_INDYGREG_PYTHON_ARCHIVE",
    (
        f"cpython-{python_version}+{indygreg_python_release_date}-"
        "x86_64-unknown-linux-gnu-install_only.tar.gz"
    ),
)
indygreg_python_download_url = os.getenv(
    "PYINFRA_INDYGREG_PYTHON_DOWNLOAD_URL",
    (
        "https://github.com/indygreg/python-build-standalone/releases/download/"
        f"{indygreg_python_release_date}/{indygreg_python_archive}"
    ),
)


# -- Container registry configuration
registry_type = os.getenv("PYINFRA_CONTAINER_REGISTRY_TYPE", "harbor2")
registry_scheme = os.getenv("PYINFRA_CONTAINER_REGISTRY_SCHEME", "http")
registry_name = os.getenv("PYINFRA_CONTAINER_REGISTRY_NAME", "bai-repo")
registry_port = os.getenv("PYINFRA_CONTAINER_REGISTRY_PORT", "7080")
registry_username = os.getenv("PYINFRA_CONTAINER_REGISTRY_USERNAME", "bai")
registry_projects = os.getenv("PYINFRA_CONTAINER_REGISTRY_PROJECTS", "bai,bai-user")
registry_password = os.getenv("PYINFRA_CONTAINER_REGISTRY_PASSWORD", "lY0B=op3")
