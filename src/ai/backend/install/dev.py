from rich.text import Text

from .context import current_log


async def install_git_lfs() -> None:
    log = current_log.get()
    log.write(Text.from_markup("[dim green]Installing Git LFS"))
    """
    case $DISTRO in
    Debian)
      $sudo apt-get install -y git-lfs
      ;;
    RedHat)
      curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | $sudo bash
      $sudo yum install -y git-lfs
      ;;
    SUSE)
      $sudo zypper install -y git-lfs
      ;;
    Darwin)
      brew install git-lfs
      ;;
    esac
    git lfs install
    """


async def install_git_hooks() -> None:
    log = current_log.get()
    log.write(Text.from_markup("[dim green]Installing Git hooks"))
    """
    local magic_str="monorepo standard pre-commit hook"
    if [ -f .git/hooks/pre-commit ]; then
      grep -Fq "$magic_str" .git/hooks/pre-commit
      if [ $? -eq 0 ]; then
        :
      else
        echo "" >> .git/hooks/pre-commit
        cat scripts/pre-commit >> .git/hooks/pre-commit
      fi
    else
      cp scripts/pre-commit .git/hooks/pre-commit
      chmod +x .git/hooks/pre-commit
    fi
    local magic_str="monorepo standard pre-push hook"
    if [ -f .git/hooks/pre-push ]; then
      grep -Fq "$magic_str" .git/hooks/pre-push
      if [ $? -eq 0 ]; then
        :
      else
        echo "" >> .git/hooks/pre-push
        cat scripts/pre-push >> .git/hooks/pre-push
      fi
    else
      cp scripts/pre-push .git/hooks/pre-push
      chmod +x .git/hooks/pre-push
    fi
    """


async def bootstrap_pants(local_execution_root_dir: str) -> None:
    log = current_log.get()
    log.write(Text.from_markup("[dim green]Bootstrapping Pantsbuild"))
    log.write(f"local_execution_root_dir = {local_execution_root_dir}")
    """
    pants_local_exec_root=$($docker_sudo $bpython scripts/check-docker.py --get-preferred-pants-local-exec-root)
    mkdir -p "$pants_local_exec_root"
    $bpython scripts/tomltool.py -f .pants.rc set 'GLOBAL.local_execution_root_dir' "$pants_local_exec_root"
    set +e
    if command -v pants &> /dev/null ; then
      echo "Pants system command is already installed."
    else
      case $DISTRO in
      Darwin)
        brew install pantsbuild/tap/pants
        ;;
      *)
        curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh > /tmp/get-pants.sh
        bash /tmp/get-pants.sh
        if ! command -v pants &> /dev/null ; then
          $sudo ln -s $HOME/bin/pants /usr/local/bin/pants
          show_note "Symlinked $HOME/bin/pants from /usr/local/bin/pants as we could not find it from PATH..."
        fi
        ;;
      esac
    fi
    pants version
    if [ $? -eq 1 ]; then
      # If we can't find the prebuilt Pants package, then try the source installation.
      show_error "Cannot proceed the installation because Pants is not available for your platform!"
      exit 1
    fi
    set -e
    """

    """
    pants export \
      --resolve=python-default \
      --resolve=python-kernel \
      --resolve=pants-plugins \
      --resolve=towncrier \
      --resolve=ruff \
      --resolve=mypy \
      --resolve=black
    """


async def install_editable_webui() -> None:
    log = current_log.get()
    log.write(Text.from_markup("[dim green]Installing the editable version of webui"))
    """
    if ! command -v node &> /dev/null; then
      install_node
    fi
    show_info "Installing editable version of Web UI..."
    if [ -d "./src/ai/backend/webui" ]; then
      echo "src/ai/backend/webui already exists, so running 'make clean' on it..."
      cd src/ai/backend/webui
      make clean
    else
      git clone https://github.com/lablup/backend.ai-webui ./src/ai/backend/webui
      cd src/ai/backend/webui
      cp configs/default.toml config.toml
      local site_name=$(basename $(pwd))
      # The debug mode here is only for 'hard-core' debugging scenarios -- it changes lots of behaviors.
      # (e.g., separate debugging of Electron's renderer and main threads)
      sed_inplace "s@debug = true@debug = false@" config.toml
      # The webserver endpoint to use in the session mode.
      sed_inplace "s@#[[:space:]]*apiEndpoint =.*@apiEndpoint = "'"'"http://127.0.0.1:${WEBSERVER_PORT}"'"@' config.toml
      sed_inplace "s@#[[:space:]]*apiEndpointText =.*@apiEndpointText = "'"'"${site_name}"'"@' config.toml
      # webServerURL lets the electron app use the web UI contents from the server.
      # The server may be either a `npm run server:d` instance or a `./py -m ai.backend.web.server` instance.
      # In the former case, you may live-edit the webui sources while running them in the electron app.
      sed_inplace "s@webServerURL =.*@webServerURL = "'"'"http://127.0.0.1:${WEBSERVER_PORT}"'"@' config.toml
      sed_inplace "s@proxyURL =.*@proxyURL = "'"'"http://127.0.0.1:${WSPROXY_PORT}"'"@' config.toml
      echo "PROXYLISTENIP=0.0.0.0" >> .env
      echo "PROXYBASEHOST=localhost" >> .env
      echo "PROXYBASEPORT=${WSPROXY_PORT}" >> .env
    fi
    npm i
    make compile
    make compile_wsproxy
    cd ../../../..
    """
