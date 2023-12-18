from __future__ import annotations

import asyncio
import shutil
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from .tomltool import toml_set

if TYPE_CHECKING:
    from .context import Context


async def install_git_lfs(ctx: Context) -> None:
    ctx.log_header("Installing Git LFS")
    if ctx.os_info.distro == "RedHat":
        await ctx.run_shell(
            "curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh"
            "| sudo bash"
        )
    await ctx.install_system_package({
        "Debian": ["git-lfs"],
        "RedHat": ["git-lfs"],
        "SUSE": ["git-lfs"],
        "Darwin": ["git-lfs"],
    })
    await ctx.run_shell("git lfs install", stderr=asyncio.subprocess.DEVNULL)


async def install_git_hooks(ctx: Context) -> None:
    ctx.log_header("Installing Git hooks")

    def upsert_hook(hook_name: str, magic: str) -> None:
        content = ""
        src_path = Path("scripts") / hook_name
        hook_path = Path(".git") / "hooks" / hook_name
        try:
            content = hook_path.read_text()
        except FileNotFoundError:
            shutil.copy(src_path, hook_path)
            hook_path.chmod(0o777)
            ctx.log.write(f"✓ Installed a new {hook_name} hook.")
            return
        if magic not in content:
            content += "\n\n" + src_path.read_text()
            hook_path.write_text(content)
            ctx.log.write(f"✓ Updated the {hook_name} hook.")
            return
        ctx.log.write(f"✓ The {hook_name} hook is already installed.")

    upsert_hook("pre-commit", "monorepo standard pre-commit hook")
    upsert_hook("pre-push", "monorepo standard pre-push hook")


async def bootstrap_pants(ctx: Context, local_execution_root_dir: str) -> None:
    ctx.log_header("Bootstrapping Pantsbuild")
    ctx.log.write(f"local_execution_root_dir = {local_execution_root_dir}")
    toml_set(".pants.rc", "GLOBAL.local_execution_root_dir", local_execution_root_dir)
    await ctx.run_shell("pants version")


async def pants_export(ctx: Context) -> None:
    ctx.log_header("Creating virtualenvs from pants export")
    await ctx.run_shell(
        textwrap.dedent(
            """
    pants export \
     --resolve=python-default \
     --resolve=towncrier \
     --resolve=ruff \
     --resolve=mypy \
     --resolve=black
    """
        )
    )


async def install_editable_webui(ctx: Context) -> None:
    ctx.log_header("Installing the editable version of webui")
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
