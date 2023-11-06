from .context import current_os
from .types import OSInfo


async def detect_os():
    """
    # Detect distribution
    KNOWN_DISTRO="(Debian|Ubuntu|RedHat|CentOS|openSUSE|Amazon|Arista|SUSE)"
    DISTRO=$(lsb_release -d 2>/dev/null | grep -Eo $KNOWN_DISTRO  || grep -Eo $KNOWN_DISTRO /etc/issue 2>/dev/null || uname -s)

    if [ $DISTRO = "Darwin" ]; then
      DISTRO="Darwin"
      STANDALONE_PYTHON_PLATFORM="apple-darwin"
    elif [ -f /etc/debian_version -o "$DISTRO" == "Debian" -o "$DISTRO" == "Ubuntu" ]; then
      DISTRO="Debian"
      STANDALONE_PYTHON_PLATFORM="unknown-linux-gnu"
    elif [ -f /etc/redhat-release -o "$DISTRO" == "RedHat" -o "$DISTRO" == "CentOS" -o "$DISTRO" == "Amazon" ]; then
      DISTRO="RedHat"
      STANDALONE_PYTHON_PLATFORM="unknown-linux-gnu"
    elif [ -f /etc/system-release -o "$DISTRO" == "Amazon" ]; then
      DISTRO="RedHat"
      STANDALONE_PYTHON_PLATFORM="unknown-linux-gnu"
    elif [ -f /usr/lib/os-release -o "$DISTRO" == "SUSE" ]; then
      DISTRO="SUSE"
      STANDALONE_PYTHON_PLATFORM="unknown-linux-gnu"
    else
      show_error "Sorry, your host OS distribution is not supported by this script."
      show_info "Please send us a pull request or file an issue to support your environment!"
      exit 1
    fi
    """
    current_os.set(
        OSInfo(
            platform="",
            distro="",
        )
    )


async def detect_cuda() -> None:
    pass


async def check_docker_desktop_mount() -> None:
    """
    echo "validating Docker Desktop mount permissions..."
    docker pull alpine:3.8 > /dev/null
    docker run --rm -v "$HOME/.pyenv:/root/vol" alpine:3.8 ls /root/vol > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      # backend.ai-krunner-DISTRO pkgs are installed in pyenv's virtualenv,
      # so ~/.pyenv must be mountable.
      show_error "You must allow mount of '$HOME/.pyenv' in the File Sharing preference of the Docker Desktop app."
      exit 1
    fi
    docker run --rm -v "$ROOT_PATH:/root/vol" alpine:3.8 ls /root/vol > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      show_error "You must allow mount of '$ROOT_PATH' in the File Sharing preference of the Docker Desktop app."
      exit 1
    fi
    echo "${REWRITELN}validating Docker Desktop mount permissions: ok"
    """
