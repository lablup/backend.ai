"""
Pyinfra subprocess runner for DevContext.

Runs pyinfra deploy scripts as a subprocess, using the gevent
workaround (run_local.py) and DevInventoryBuilder for @local deployment.

This bridges the async TUI installer with pyinfra's synchronous
greenlet-based execution model.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import InstallInfo, InstallVariable
    from .widgets import SetupLog


def _find_run_local() -> Path:
    """Find the run_local.py script path."""
    return Path(__file__).parent / "pyinfra" / "inventory" / "run_local.py"


def _find_deploy_script(service: str) -> Path:
    """Find the deploy script for a given service."""
    deploy_root = Path(__file__).parent / "pyinfra" / "deploy" / "cores"
    mapping = {
        "manager": deploy_root / "manager" / "deploy.py",
        "agent": deploy_root / "agent" / "deploy.py",
        "storage_proxy": deploy_root / "storage_proxy" / "deploy.py",
        "webserver": deploy_root / "webserver" / "deploy.py",
        "appproxy_coordinator": deploy_root / "appproxy" / "coordinator" / "deploy.py",
        "appproxy_worker_interactive": (
            deploy_root / "appproxy" / "worker_interactive" / "deploy.py"
        ),
        "appproxy_worker_tcp": deploy_root / "appproxy" / "worker_tcp" / "deploy.py",
        "appproxy_worker_inference": deploy_root / "appproxy" / "worker_inference" / "deploy.py",
        "appproxy_traefik": deploy_root / "appproxy" / "traefik" / "deploy.py",
    }
    path = mapping.get(service)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Deploy script not found for service: {service}")
    return path


def _build_inventory_file(
    install_info: InstallInfo,
    install_variable: InstallVariable,
    mode: str = "configure_only",
) -> str:
    """
    Build a temporary pyinfra inventory file from InstallInfo.

    Returns the path to the temporary file.
    """
    inventory_code = f"""\
from ai.backend.install.pyinfra.inventory.dev_inventory import DevInventoryBuilder

builder = DevInventoryBuilder(
    public_facing_address="{install_variable.public_facing_address}",
    home_dir="{install_info.base_path}",
    bai_version="{install_info.version}",
)
result = builder.build()

# Override mode and skip_systemd
for key, val in result.items():
    if isinstance(val, list):
        for item in val:
            if isinstance(item, tuple) and len(item) == 2:
                _, data = item
                if isinstance(data, dict):
                    data["mode"] = "{mode}"
                    data["skip_systemd"] = True

mgmt = result["mgmt"]
compute = result.get("compute", [])
agent = result.get("agent", [])
mgr = result.get("mgr", [])
web = result.get("web", [])
sp = result.get("sp", [])
apc = result.get("apc", [])
apw = result.get("apw", [])
dashboard = result.get("dashboard", [])
"""
    fd, path = tempfile.mkstemp(suffix=".py", prefix="pyinfra-inventory-")
    with os.fdopen(fd, "w") as f:
        f.write(inventory_code)
    return path


async def run_pyinfra_deploy(
    service: str,
    install_info: InstallInfo,
    install_variable: InstallVariable,
    mode: str = "configure_only",
    dry_run: bool = False,
    log: SetupLog | None = None,
) -> int:
    """
    Run a pyinfra deploy script as a subprocess.

    Args:
        service: Service name (e.g., "manager", "agent", "appproxy_coordinator")
        install_info: Current installation configuration
        install_variable: Install variables (public_facing_address, etc.)
        mode: Deploy mode ("configure_only", "install", "update")
        dry_run: If True, run with --dry flag
        log: Optional TUI log widget for output

    Returns:
        Exit code (0 = success)
    """
    run_local = _find_run_local()
    deploy_script = _find_deploy_script(service)
    inventory_path = _build_inventory_file(install_info, install_variable, mode)

    try:
        python = sys.executable
        cmd = [python, str(run_local)]
        if dry_run:
            cmd.append("--dry")
        cmd.extend([str(inventory_path), str(deploy_script)])

        env = os.environ.copy()
        src_path = str(Path(__file__).parent.parent.parent.parent)
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{src_path}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = src_path
        env["PYINFRA_SUDO_PASSWORD"] = ""

        if log:
            log.write(f"Running pyinfra {mode} for {service}...")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
            cwd=str(install_info.base_path),
        )

        if proc.stdout is not None:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode().rstrip()
                if log and text:
                    log.write(text)

        await proc.wait()
        return proc.returncode or 0

    finally:
        Path(inventory_path).unlink(missing_ok=True)
