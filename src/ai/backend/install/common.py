from .types import OSInfo, Platform


async def detect_os() -> OSInfo:
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
    return OSInfo(
        platform=Platform.LINUX_ARM64,
        distro="",
    )


async def detect_cuda() -> None:
    pass
