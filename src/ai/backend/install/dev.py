from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text

if TYPE_CHECKING:
    from .context import Context


async def install_git_lfs(ctx: Context) -> None:
    ctx.log.write(Text.from_markup("[dim green]Installing Git LFS"))
    if ctx.os_info.distro == "RedHat":
        "curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | $sudo bash"
    await ctx.install_system_package(
        {
            "Debian": ["git-lfs"],
            "RedHat": ["git-lfs"],
            "SUSE": ["git-lfs"],
            "Darwin": ["git-lfs"],
        }
    )
    await ctx.run_shell("git lfs install")


async def install_git_hooks(ctx: Context) -> None:
    ctx.log.write(Text.from_markup("[dim green]Installing Git hooks"))
    await ctx.run_shell("""
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
    """)


async def bootstrap_pants(ctx: Context, local_execution_root_dir: str) -> None:
    ctx.log.write(Text.from_markup("[dim green]Bootstrapping Pantsbuild"))
    ctx.log.write(f"local_execution_root_dir = {local_execution_root_dir}")
    await ctx.run_shell("""
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
    """)
    await ctx.run_shell("""
    pants export \
      --resolve=python-default \
      --resolve=python-kernel \
      --resolve=pants-plugins \
      --resolve=towncrier \
      --resolve=ruff \
      --resolve=mypy \
      --resolve=black
    """)


async def install_editable_webui(ctx: Context) -> None:
    ctx.log.write(Text.from_markup("[dim green]Installing the editable version of webui"))
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
