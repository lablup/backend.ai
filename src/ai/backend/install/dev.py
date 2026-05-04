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
     --resolve=python-kernel \
     --resolve=towncrier \
     --resolve=mypy
    """
        )
    )


async def get_current_branch() -> str:
    """Get the current git branch name."""
    proc = await asyncio.create_subprocess_exec(
        "git",
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await proc.communicate()
    return stdout.decode().strip()


async def install_editable_webui(ctx: Context) -> None:
    ctx.log_header("Installing the editable version of webui")
    webui_path = ctx.install_info.base_path / "src" / "ai" / "backend" / "webui"

    if webui_path.exists():
        ctx.log.write("src/ai/backend/webui already exists, cleaning and pulling latest...")
        await ctx.run_shell("make clean", cwd=webui_path)
        await ctx.run_shell(
            "git pull --ff-only || echo 'Local changes exist, skipping pull...'", cwd=webui_path
        )
    else:
        ctx.log.write("Cloning backend.ai-webui repository...")
        await ctx.run_shell(
            "git clone https://github.com/lablup/backend.ai-webui ./src/ai/backend/webui"
        )
        # Copy and configure config.toml
        config_src = webui_path / "configs" / "default.toml"
        config_dst = webui_path / "config.toml"
        shutil.copy(config_src, config_dst)

        service = ctx.install_info.service_config
        webserver_port = service.webserver_addr.face.port
        wsproxy_port = service.local_proxy_addr.face.port

        config_path = str(config_dst)
        toml_set(config_path, "general.debug", "false")
        toml_set(config_path, "general.apiEndpoint", f"http://127.0.0.1:{webserver_port}")
        toml_set(config_path, "general.apiEndpointText", "Backend.AI")
        toml_set(config_path, "general.webServerURL", f"http://127.0.0.1:{webserver_port}")
        toml_set(config_path, "general.proxyURL", f"http://127.0.0.1:{wsproxy_port}")

        # Configure .env
        env_path = webui_path / ".env"
        env_path.write_text(
            f"PROXYLISTENIP=0.0.0.0\nPROXYBASEHOST=localhost\nPROXYBASEPORT={wsproxy_port}\n"
        )

    # Install dependencies and build
    ctx.log.write("Installing pnpm dependencies...")
    await ctx.run_shell("pnpm i", cwd=webui_path)
    ctx.log.write("Compiling webui...")
    await ctx.run_shell("make compile", cwd=webui_path)
